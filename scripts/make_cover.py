from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
im=Image.new('RGB',(1200,630),'#f4f2eb');d=ImageDraw.Draw(im)
font='/System/Library/Fonts/Supplemental/Arial.ttf'
bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
f=lambda n:ImageFont.truetype(font,n)
b=lambda n:ImageFont.truetype(bold,n)
d.rounded_rectangle((54,48,91,85),radius=9,fill='#e85a32');d.polygon([(67,58),(80,67),(67,76)],fill='#fffefa');d.text((105,51),'FRAME INDEX',font=b(25),fill='#242720');d.text((54,126),'Small prompts.',font=b(73),fill='#242720');d.text((54,208),'Big motion.',font=b(73),fill='#e85a32');d.text((57,313),'703 posts. 712 videos. The prompts behind the pixels.',font=f(23),fill='#74766e')
slugs=['ror-fly-880547','twoclipping-402193','godsboy7777-150194','fanfulladev-063524']
for i,slug in enumerate(slugs):
 path=ROOT/'docs/assets/thumbs'/(slug+'.webp')
 thumb=Image.open(path).convert('RGB').resize((261,163))
 im.paste(thumb,(54+i*278,402))
im.save(ROOT/'docs/assets/social-cover.jpg',quality=90)
print('Created social cover')
