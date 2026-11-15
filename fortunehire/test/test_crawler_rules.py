import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from crawler_rules import CrawlerRules
import collect_jobs as c
class RulesTests(unittest.TestCase):
 def rules(self,body):
  r=CrawlerRules();r.parse(body.splitlines());return r
 def test_specific_career_allow_beats_root_disallow_in_either_order(self):
  for body in ['User-agent: *\nDisallow: /\nAllow: /careers\nAllow: /api/pcsx','User-agent: *\nAllow: /careers\nAllow: /api/pcsx\nDisallow: /']:
   r=self.rules(body)
   for path in ['/careers','/careers/job/123','/api/pcsx/search']:self.assertTrue(r.can_fetch(c.UA,'https://example.com'+path))
   for path in ['/admin','/api/private']:self.assertFalse(r.can_fetch(c.UA,'https://example.com'+path))
 def test_specific_block_and_equal_allow_win_independent_of_line_order(self):
  r=self.rules('User-agent: *\nAllow: /careers\nDisallow: /careers/private\nAllow: /careers/private/public\nDisallow: /same\nAllow: /same')
  self.assertFalse(r.can_fetch(c.UA,'/careers/private/role'));self.assertTrue(r.can_fetch(c.UA,'/careers/private/public/role'));self.assertTrue(r.can_fetch(c.UA,'/same'))
 def test_wildcards_query_and_end_anchor(self):
  r=self.rules('User-agent: *\nDisallow: /*.pdf$\nDisallow: /*?secret=\nDisallow: /\nAllow: /$')
  self.assertTrue(r.can_fetch(c.UA,'https://example.com/'));self.assertFalse(r.can_fetch(c.UA,'https://example.com/role.pdf'));self.assertFalse(r.can_fetch(c.UA,'/role?secret=x'));self.assertFalse(r.can_fetch(c.UA,'/role'))
  r=self.rules('User-agent: *\nDisallow: /*.pdf$');self.assertTrue(r.can_fetch(c.UA,'/role.pdf?view=1'))
 def test_specific_user_agent_groups_merge_without_inheriting_wildcard(self):
  r=self.rules('User-agent: *\nDisallow: /\nUser-agent: FortuneHirePilot\nDisallow: /one\nUser-agent: fortunehirepilot\nDisallow: /two')
  self.assertTrue(r.can_fetch(c.UA,'/careers'));self.assertFalse(r.can_fetch(c.UA,'/one'));self.assertFalse(r.can_fetch(c.UA,'/two'));self.assertFalse(r.can_fetch('OtherBot/1','/careers'))
 def test_octet_normalization_keeps_encoded_reserved_characters_distinct(self):
  r=self.rules('User-agent: *\nDisallow: /foo/bar\nDisallow: /café\nDisallow: /literal%2A')
  self.assertFalse(r.can_fetch(c.UA,'/foo/%62ar'));self.assertFalse(r.can_fetch(c.UA,'/caf%C3%A9'));self.assertFalse(r.can_fetch(c.UA,'/literal%2a'))
  self.assertFalse(r.can_fetch(c.UA,'/literal*'));self.assertTrue(r.can_fetch(c.UA,'/foo%2Fbar'));self.assertTrue(r.can_fetch(c.UA,'/literalZZ'))
  self.assertFalse(self.rules('User-agent: *\nDisallow: /literal%24').can_fetch(c.UA,'/literal$'))
 def test_pacing_sitemaps_empty_rules_and_bom(self):
  r=CrawlerRules();self.assertFalse(r.can_fetch(c.UA,'/careers'));r.parse([]);self.assertTrue(r.can_fetch(c.UA,'/careers'))
  r=self.rules('\ufeffUser-agent: *\nDisallow:\nCrawl-delay: 2.5\nSitemap: https://example.com/site.xml\nDisallow: /private # note')
  self.assertEqual(r.crawl_delay(c.UA),2.5);self.assertEqual(r.site_maps(),['https://example.com/site.xml']);self.assertFalse(r.can_fetch(c.UA,'/private'));self.assertTrue(r.can_fetch(c.UA,'/robots.txt'))
 def test_client_uses_specific_path_precedence_and_preserves_pacing(self):
  with patch.object(c.Client,'get',return_value=(200,'User-agent: *\nDisallow: /\nAllow: /careers\nCrawl-delay: 3')):
   cl=c.Client('example.com');self.assertTrue(cl.robots.can_fetch(c.UA,'https://example.com/careers'));self.assertFalse(cl.robots.can_fetch(c.UA,'https://example.com/private'));self.assertEqual(cl.delay,3)
