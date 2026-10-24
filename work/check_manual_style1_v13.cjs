const {chromium}=require('C:/Users/liu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path=require('node:path');
const fs=require('node:fs');
const {pathToFileURL}=require('node:url');
(async()=>{
  const root=path.resolve(__dirname,'..'),out=path.join(root,'outputs','ATX-Desk-v13');
  const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1});
  await context.setOffline(true);
  const page=await context.newPage();const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.join(out,'Style1_V13_Assembly_Manual.html')).href);
  await page.evaluate(async()=>{for(const im of document.images){im.loading='eager';await im.decode();}await document.fonts.ready;});
  const stats=await page.evaluate(()=>({title:document.title,parts:document.querySelectorAll('.part-card').length,
    steps:document.querySelectorAll('.step').length,images:[...document.images].map(i=>({ok:i.complete&&i.naturalWidth>0,w:i.naturalWidth,h:i.naturalHeight})),
    checkboxes:document.querySelectorAll('.check input').length,desktopOverflow:document.documentElement.scrollWidth>innerWidth}));
  await page.screenshot({path:path.join(out,'Manual_Images','browser-desktop.png')});
  await page.locator('#step08').screenshot({path:path.join(out,'Manual_Images','browser-step08.png')});
  await page.locator('#N18').screenshot({path:path.join(out,'Manual_Images','browser-insert-detail.png')});
  await page.locator('.check input').first().check();
  const checked=await page.locator('#progress').textContent();
  await page.reload();await page.locator('.check input').first().waitFor();
  stats.checkboxPersistence=await page.locator('.check input').first().isChecked();
  await page.locator('#reset').click();stats.resetWorks=await page.locator('.check input:checked').count()===0;
  stats.progressAfterCheck=checked;
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(out,'Manual_Images','browser-mobile.png')});
  stats.mobileOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  await page.locator('#P13').screenshot({path:path.join(out,'Manual_Images','browser-mobile-part.png')});
  await page.emulateMedia({media:'print'});
  stats.printToolbarHidden=await page.locator('.toolbar').evaluate(e=>getComputedStyle(e).display==='none');
  stats.errors=errors;stats.offline=true;
  if(stats.parts!==17||stats.steps!==13||stats.images.some(i=>!i.ok)||stats.mobileOverflow||stats.desktopOverflow||!stats.checkboxPersistence||!stats.resetWorks||errors.length)throw Error(JSON.stringify(stats));
  fs.writeFileSync(path.join(out,'manual_browser_verification.json'),JSON.stringify(stats,null,2));
  console.log(JSON.stringify({...stats,images:stats.images.length}));
  await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1;});
