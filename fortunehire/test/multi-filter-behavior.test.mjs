import test from 'node:test';
import assert from 'node:assert/strict';
import {installMultiFilterBehavior} from '../public/multi-filter-behavior.js';

function fixture(){
  const listeners=new Map();
  const make=()=>({open:false,contains(target){return target===this||target.parent===this;}});
  const [state,arrangement,jobFunction]=[make(),make(),make()];
  const document={querySelectorAll:()=>[state,arrangement,jobFunction],addEventListener(type,fn){listeners.set(type,fn);}};
  installMultiFilterBehavior(document);
  return {state,arrangement,jobFunction,send:(type,target,extra={})=>listeners.get(type)({target,...extra})};
}

test('outside pointer click or touch closes open dropdowns',()=>{
  const f=fixture();f.state.open=true;f.send('pointerdown',{});assert.equal(f.state.open,false);
});

test('opening another dropdown closes the previous one',()=>{
  const f=fixture();f.state.open=true;f.arrangement.open=true;f.send('toggle',f.arrangement);
  assert.equal(f.state.open,false);assert.equal(f.arrangement.open,true);
});

test('Escape closes the active dropdown',()=>{
  const f=fixture();f.jobFunction.open=true;f.send('keydown',{}, {key:'Escape'});
  assert.equal(f.jobFunction.open,false);
});

test('checkbox pointer interaction remains inside and does not close dropdown',()=>{
  const f=fixture();f.state.open=true;const checkbox={parent:f.state};
  f.send('pointerdown',checkbox);assert.equal(f.state.open,true);
});
