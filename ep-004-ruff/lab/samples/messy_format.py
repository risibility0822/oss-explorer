def  price_with_tax( price,rate = 0.05 ):
  total=price*(1+rate)
  return {'價格':price,'含稅':round(total),'說明':"含 5% 營業稅"}
items = [ 120,
   350,980 ]
print( [price_with_tax(p) for p in items] )
