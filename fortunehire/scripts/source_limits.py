"""Per-source request and sample budgets; published crawler delays still apply."""
def policy(registry,company):
 source=registry.get('sources',{}).get(company,{})
 values={key:source.get(key,default) for key,default in [('maxTracked',100),('maxNew',20),('requestDelaySeconds',1)]}
 for key,upper in [('maxTracked',100),('maxNew',20),('requestDelaySeconds',60)]:
  v=values[key]
  if isinstance(v,bool) or not isinstance(v,(int,float)) or not 1<=v<=upper or key!='requestDelaySeconds' and not isinstance(v,int):raise ValueError('Invalid source collection budget: '+key)
 return values
