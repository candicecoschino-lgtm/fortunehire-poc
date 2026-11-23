const MAX_FILE_BYTES = 10 * 1024 * 1024;
const MAX_XML_BYTES = 2 * 1024 * 1024;
const MAX_PAGES = 30;
const WORD_NAMESPACES = [
  'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
  'http://purl.oclc.org/ooxml/wordprocessingml/main',
];

export class ResumeFileError extends Error {}

export function fileKind(file) {
  const extension = file.name.split('.').at(-1)?.toLowerCase();
  if (!['pdf', 'docx'].includes(extension)) throw new ResumeFileError('Choose a PDF or DOCX file, or paste your experience below.');
  if (!file.size || file.size > MAX_FILE_BYTES) throw new ResumeFileError('Choose a nonempty file up to 10 MB, or paste your experience below.');
  return extension;
}

function documentEntry(buffer) {
  const view = new DataView(buffer);
  const invalid = () => new ResumeFileError('This DOCX archive is unsupported or damaged. Save a new DOCX copy or paste its text.');
  // Locate the ZIP end record, allowing a bounded comment.
  let end = view.byteLength - 22;
  const first = Math.max(0, end - 65_535);
  while (end >= first && (view.getUint32(end, true) !== 0x06054b50 || end + 22 + view.getUint16(end + 20, true) !== view.byteLength)) end--;
  if (end < first || view.getUint16(end + 4, true) || view.getUint16(end + 6, true)) throw invalid();
  const entries = view.getUint16(end + 10, true);
  const size = view.getUint32(end + 12, true);
  let offset = view.getUint32(end + 16, true);
  if (!entries || entries > 1000 || entries !== view.getUint16(end + 8, true) || offset + size !== end) throw invalid();
  const directoryStart = offset;
  const decoder = new TextDecoder();
  let document;
  let hasContentTypes = false;
  for (let i = 0; i < entries; i++) {
    if (offset + 46 > end || view.getUint32(offset, true) !== 0x02014b50) throw invalid();
    const flags = view.getUint16(offset + 8, true);
    const method = view.getUint16(offset + 10, true);
    const compressed = view.getUint32(offset + 20, true);
    const expanded = view.getUint32(offset + 24, true);
    const nameLength = view.getUint16(offset + 28, true);
    const next = offset + 46 + nameLength + view.getUint16(offset + 30, true) + view.getUint16(offset + 32, true);
    if (next > end) throw invalid();
    const name = decoder.decode(new Uint8Array(buffer, offset + 46, nameLength));
    if (name === '[Content_Types].xml') hasContentTypes = true;
    if (name.toLowerCase().includes('vbaproject')) throw invalid();
    if (name === 'word/document.xml') {
      const entry = view.getUint32(offset + 42, true);
      if (document || flags & 1 || ![0, 8].includes(method) || !expanded || expanded > MAX_XML_BYTES
          || !compressed || entry + 30 > directoryStart || view.getUint32(entry, true) !== 0x04034b50
          || view.getUint16(entry + 6, true) !== flags || view.getUint16(entry + 8, true) !== method) throw invalid();
      const localNameLength = view.getUint16(entry + 26, true);
      const start = entry + 30 + localNameLength + view.getUint16(entry + 28, true);
      if (start + compressed > directoryStart
          || decoder.decode(new Uint8Array(buffer, entry + 30, localNameLength)) !== name) throw invalid();
      document = {bytes: new Uint8Array(buffer, start, compressed), expanded, method};
    }
    offset = next;
  }
  if (!document || !hasContentTypes || offset !== end) throw invalid();
  return document;
}

export async function docxXml(buffer, signal) {
  signal?.throwIfAborted();
  const {bytes, expanded, method} = documentEntry(buffer);
  if (method === 0 && bytes.length === expanded) return new TextDecoder('utf-8', {fatal: true}).decode(bytes);
  if (method !== 8) throw new ResumeFileError('The DOCX document size is invalid. Paste its text below.');
  const reader = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw')).getReader();
  const cancel = () => { reader.cancel().catch(() => {}); };
  signal?.addEventListener('abort', cancel, {once: true});
  const result = new Uint8Array(expanded);
  let offset = 0;
  try {
    for (;;) {
      const {done, value} = await reader.read();
      signal?.throwIfAborted();
      if (done) break;
      if (offset + value.length > result.length) throw new ResumeFileError('The DOCX document exceeds its declared size. Paste its text below.');
      result.set(value, offset);
      offset += value.length;
    }
  } finally {
    signal?.removeEventListener('abort', cancel);
    await reader.cancel().catch(() => {});
  }
  if (offset !== expanded) throw new ResumeFileError('The DOCX document is incomplete. Paste its text below.');
  return new TextDecoder('utf-8', {fatal: true}).decode(result);
}

function wordText(xml) {
  if (/<\s*!\s*(?:DOCTYPE|ENTITY)\b/i.test(xml)) throw new ResumeFileError('The DOCX contains unsupported XML declarations. Paste its text below.');
  const tree = new DOMParser().parseFromString(xml, 'application/xml');
  const root = tree.documentElement;
  if (root.localName !== 'document' || !WORD_NAMESPACES.includes(root.namespaceURI)) {
    throw new ResumeFileError('The DOCX body could not be read. Paste its text below.');
  }
  const namespace = root.namespaceURI;
  return Array.from(root.getElementsByTagNameNS(namespace, 'p'), paragraph =>
    Array.from(paragraph.getElementsByTagNameNS(namespace, 't'), run => run.textContent).join('')
  ).join('\n');
}

async function pdfText(buffer, signal) {
  if (new TextDecoder().decode(buffer.slice(0, 5)) !== '%PDF-') {
    throw new ResumeFileError('This file does not have a PDF signature. Choose another file or paste its text.');
  }
  const {getDocument, PDFWorker} = await import('./vendor/pdfjs/pdf.min.mjs');
  signal.throwIfAborted();
  // An explicit port gives this extraction its own cancellable worker.
  const port = new Worker(new URL('./vendor/pdfjs/pdf.worker.min.mjs', import.meta.url), {type: 'module'});
  const worker = new PDFWorker({port, verbosity: 0});
  const task = getDocument({
    data: new Uint8Array(buffer), worker, verbosity: 0, isEvalSupported: false,
    useWasm: false, useWorkerFetch: false, disableFontFace: true, useSystemFonts: false,
    disableWorkerRendering: true,
  });
  let abort;
  const cancelled = new Promise((_, reject) => {
    abort = () => reject(signal.reason);
    signal.addEventListener('abort', abort, {once: true});
  });
  const read = async () => {
    const pdf = await task.promise;
    if (pdf.numPages > MAX_PAGES) throw new ResumeFileError(`The PDF exceeds ${MAX_PAGES} pages. Choose a shorter copy or paste its text.`);
    let text = '';
    for (let page = 1; page <= pdf.numPages; page++) {
      const content = await (await pdf.getPage(page)).getTextContent();
      text += content.items.map(item => item.str ? item.str + (item.hasEOL ? '\n' : ' ') : '').join('') + '\n';
      if (text.length > 60_000) break;
    }
    return text;
  };
  try {
    return await Promise.race([read(), cancelled]);
  } catch (error) {
    if (error.name === 'PasswordException') {
      throw new ResumeFileError('This PDF is password protected. Open an unlocked copy or paste its text.');
    }
    throw error;
  } finally {
    signal.removeEventListener('abort', abort);
    // Destroy the document before terminating the worker on the successful path.
    // On cancellation the worker may be busy and unable to acknowledge cleanup.
    const destroy = task.destroy().catch(() => {});
    if (!signal.aborted) await destroy;
    worker.destroy();
    port.terminate();
  }
}

export async function extractResume(file, signal) {
  const kind = fileKind(file);
  const buffer = await file.arrayBuffer();
  signal.throwIfAborted();
  const text = kind === 'pdf' ? await pdfText(buffer, signal) : wordText(await docxXml(buffer, signal));
  if (!text || text.replace(/\s/g, '').length < 30) {
    throw new ResumeFileError('Very little text was found. Scanned documents need a text copy you can paste below.');
  }
  return text;
}
