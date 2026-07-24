# CDP Knowledge Source Rename Script

Rename Copilot Studio knowledge sources via Chrome DevTools Protocol (CDP).
Use when playwright-cli auth is expired and Kiro Chrome has a valid session on port 9223.

## Prerequisites
- Kiro Chrome running with `--remote-debugging-port=9223`
- Node.js with `ws` module (`npm install -g ws`)

## Usage

```bash
# Interactive: rename one source
NODE_PATH=$(npm root -g) node -e "
const WebSocket = require('ws'), http = require('http');
http.get('http://127.0.0.1:9223/json', (res) => {
  let o=''; res.on('data',c=>o+=c); res.on('end',()=>{
    const p=JSON.parse(o)[0], ws=new WebSocket(p.webSocketDebuggerUrl);
    let id=0,cbs={};
    function s(m,a){const i=++id;ws.send(JSON.stringify({id:i,method:m,params:a}));return new Promise(r=>cbs[i]=r)}
    ws.on('message',msg=>{const r=JSON.parse(msg);if(r.id&&cbs[r.id]){cbs[r.id](r);delete cbs[r.id]}});
    
    async function rename(oldText, newName) {
      // Find row
      var f = await s('Runtime.evaluate',{
        expression: 'for(var i=0,rs=document.querySelectorAll(\"[role=row]\");i<rs.length;i++){if(rs[i].textContent.includes(\"'+oldText+'\"))return i;}return -1;'
      });
      var idx = f.result.result.value;
      if(idx < 0) return console.log('NOT FOUND:', oldText);
      
      // Close any open panel
      await s('Input.dispatchKeyEvent', {type:'keyDown',key:'Escape',windowsVirtualKeyCode:27});
      await new Promise(r => setTimeout(r, 1500));
      
      // Click More
      await s('Runtime.evaluate', {
        expression: 'document.querySelectorAll(\"[role=row]\")['+idx+'].querySelector(\"[aria-label=\\\"More\\\"]\").click();'
      });
      await new Promise(r => setTimeout(r, 2000));
      
      // Click Edit
      await s('Runtime.evaluate', {
        expression: 'for(var i=0,its=document.querySelectorAll(\"[role=menuitem]\");i<its.length;i++){if(its[i].textContent.trim()===\"Edit\"&&its[i].offsetParent!==null){its[i].click();break;}}'
      });
      await new Promise(r => setTimeout(r, 3000));
      
      // Set name using native value setter (REQUIRED for React inputs)
      await s('Runtime.evaluate', {
        expression: 'for(var i=0,ins=document.querySelectorAll(\"input[placeholder=\\\"Enter name\\\"]\");i<ins.length;i++){if(ins[i].offsetParent!==null){var nv=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,\"value\").set;nv.call(ins[i],\"'+newName.replace(/\"/g,'\\\\\"')+'\");ins[i].dispatchEvent(new Event(\"input\",{bubbles:true}));ins[i].dispatchEvent(new Event(\"change\",{bubbles:true}));ins[i].dispatchEvent(new Event(\"blur\",{bubbles:true}));break;}}'
      });
      await new Promise(r => setTimeout(r, 1500));
      
      // Click Save
      await s('Runtime.evaluate', {
        expression: 'for(var i=0,bs=document.querySelectorAll(\"button\");i<bs.length;i++){if(bs[i].textContent.trim()===\"Save\"&&bs[i].offsetParent!==null){bs[i].click();break;}}'
      });
      await new Promise(r => setTimeout(r, 2500));
      
      console.log('RENAMED:', oldText, '→', newName);
    }
    
    ws.on('open', async() => {
      await rename('OLD_TEXT_TO_MATCH', 'New Clean Name');
      ws.close(); process.exit(0);
    });
  });
});
"
```

## Pitfalls

1. **Save doesn't persist:** The Save button may close the panel without saving. Make sure to:
   - Use native value setter (`Object.getOwnPropertyDescriptor(...).set`) — Copilot Studio uses React-controlled inputs
   - Dispatch `input`, `change`, AND `blur` events
   - Press Enter on the input before clicking Save
   
2. **Row index is -1:** The knowledge grid uses lazy rendering. Scroll the page to make the target row visible before searching. Or navigate away and back to reset the view.

3. **More button click opens wrong row's menu:** Wait 2s for the menu to render. If clicked too fast, the previous row's menu may still be open.

4. **WebSocket disconnects during batch operations:** Long-running scripts (>30s idle) may disconnect. Break into batches of 2-3 renames per connection, or add periodic heartbeat calls.

5. **Renames don't show in grid until refresh:** After saving, the grid may still show the old name. Navigate away and back to verify persistence.

## Knowledge Source Description Fields

All file-based knowledge sources in Copilot Studio get auto-generated descriptions:
"This knowledge source searches information contained in [filename]"

Replace these with meaningful descriptions that help the AI understand what the source covers.
The description textarea uses `placeholder="Enter description"` and requires the same native value setter approach as the name field.
