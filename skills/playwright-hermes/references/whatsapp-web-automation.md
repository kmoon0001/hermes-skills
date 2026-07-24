# WhatsApp Web Automation with Playwright Hermes

## Overview
This reference covers automating WhatsApp Web using the playwright-hermes skill. WhatsApp Web requires initial QR code login, after which sessions can be persisted similar to Kiro/Copilot Studio auth.

## Prerequisites
- WhatsApp installed on mobile device
- Phone with camera for QR code scanning
- Active internet connection on both devices

## Login Process (First Time)

### 1. Navigate to WhatsApp Web
```bash
npx playwright-cli --session wa-session open https://web.whatsapp.com
```

### 2. Handle QR Code Login
The page will show:
- "Scan to log in" header
- Instructions: 
  1. Scan the QR code with your phone's camera
  2. Tap the link to open WhatsApp
  3. Scan the QR code again to link to your account
- QR code image (typically visible in the browser)

### 3. Complete Login on Phone
1. Open WhatsApp on your phone
2. Go to Settings → Linked Devices → Link a Device
3. Point camera at QR code on screen
4. Wait for connection (usually 5-10 seconds)

### 4. Verify Login Success (CRITICAL STEP)
After scanning, the page should transition to the WhatsApp Web interface.

**To verify you are actually logged in (not just seeing a loading screen):**
- Take a snapshot: `npx playwright-cli --session wa-session snapshot`
- Look for these **definitive signs of logged-in state**:
  - Element with `[data-testid="chat-list"]` (chat list on left)
  - Element with `[data-testid="cell-frame-container"]` or `[data-testid="conversation-panel-header"]` (chat header)
  - Search input with placeholder like "Search or start new chat"
  - "New chat" button (typically `[data-testid="btn-new-chat"]`)
  - Your profile picture/status in the sidebar

**If you still see:**
- "Scan to log in" text
- Instructions about scanning QR code
- WhatsApp logo with "Scan this QR code to link a device!"
- Download buttons

**Then you are NOT logged in** - you need to repeat the phone QR scanning process.

**Common mistake:** Users sometimes see a brief flash of the chat interface before being redirected back to the login screen, indicating an expired or invalid session.

## Session Persistence

### Export Auth State (After Successful Login)
```bash
npx playwright-cli --session wa-session state-save 'C:\\Users\\kevin\\.hermes-browser-session\\whatsapp-auth.json'
```

### Reuse Saved Session
```bash
npx playwright-cli --session wa-session open https://web.whatsapp.com
npx playwright-cli --session wa-session state-load 'C:\\Users\\kevin\\.hermes-browser-session\\whatsapp-auth.json'
# Should load directly to chat list if session is still valid
```

## Common Automation Patterns

### Sending a Message
```bash
# Start session and load auth
npx playwright-cli --session wa-session open https://web.whatsapp.com
npx playwright-cli --session wa-session state-load 'C:\\Users\\kevin\\.hermes-browser-session\\whatsapp-auth.json'

# Wait for chat list to load
npx playwright-cli --session wa-session sleep 3

# Search for contact/group
npx playwright-cli --session wa-session snapshot
# Find search input ref (typically accessible via placeholder or label)
npx playwright-cli --session wa-session fill <search-ref> "Contact Name"
npx playwright-cli --session wa-session sleep 2

# Select contact from results
npx playwright-cli --session wa-session click <contact-ref>
npx playwright-cli --session wa-session sleep 2

# Type and send message
npx playwright-cli --session wa-session fill <message-input-ref> "Hello from Hermes!"
npx playwright-cli --session wa-session press Enter

# Verify message sent (look for sent timestamp/checkmarks)
npx playwright-cli --session wa-session screenshot ~/whatsapp-sent-message.png
```

### Reading Recent Messages
```bash
# After loading session and navigating to chat
npx playwright-cli --session wa-session snapshot

# Find message container - look for elements with message content
# Messages typically appear in divs with specific classes/data attributes
npx playwright-cli --session wa-session eval "
  const messages = Array.from(document.querySelectorAll('[data-testid=\"msg-container\"]'));
  const lastMessage = messages[messages.length - 1];
  console.log('Last message:', lastMessage.innerText);
"

# Or get all messages in current view
npx playwright-cli --session wa-session eval "
  const messages = Array.from(document.querySelectorAll('.selectable-text, .copyable-text'));
  const recentMessages = messages.slice(-5).map(m => m.innerText.trim());
  console.log('Recent messages:', recentMessages);
"
```

## Pitfalls and Solutions

### 1. "Session Expired" or Login Required Again
**Symptom:** Redirected back to QR code page despite having saved auth
**Solution:** 
- Re-run the QR code login process
- Export fresh auth state after successful login
- WhatsApp Web sessions typically expire after periods of inactivity

### 2. Element Selectors Change Frequently
**Symptom:** Click/fill operations fail because refs don't match expected elements
**Solution:**
- Always take a snapshot before interacting to see current refs
- Use multiple identification strategies (text content, position, attributes)
- Consider using relative positioning when exact selectors fail

### 3. Media Loading Delays
**Symptom:** Screenshots show loading spinners or missing content
**Solution:**
- Add appropriate waits after navigation/actions
- Use `networkidle` state or wait for specific elements to appear
- Consider explicit waits for message send/receive confirmation

### 4. Phone Connection Required
**Symptom:** "Phone not connected" error appears in WhatsApp Web
**Solution:**
- Ensure phone has internet connection
- Keep WhatsApp app open or running in background
- Re-link device if connection is lost

## Visual Verification Checklist
Use `vision_analyze` on screenshots to verify:

1. **Login Page:**
   - QR code visible
   - Instruction text present
   - WhatsApp logo shown

2. **Chat List (After Login):**
   - Search bar visible
   - Chat conversations listed
   - New chat button present
   - User profile visible in sidebar

3. **Active Chat:**
   - Message input box at bottom
   - Send button (paper plane icon)
   - Message history visible
   - Contact name/header at top

4. **Message Sent:**
   - Sent timestamp appears
   - Checkmarks visible (single → double)
   - Message appears in chat history

## Integration with Hermes Workflows

### Basic Message Relay Pattern
```bash
# Monitor for incoming WhatsApp messages (simplified)
# In practice, this would need more sophisticated state tracking

npx playwright-cli --session wa-session open https://web.whatsapp.com
npx playwright-cli --session wa-session state-load 'C:\\Users\\kevin\\.hermes-browser-session\\whatsapp-auth.json'

# Poll for new messages every 30 seconds
while true; do
  # Get latest message timestamp/content
  LATEST_MSG=$(npx playwright-cli --session wa-session eval "
    const msgs = Array.from(document.querySelectorAll('[data-testid=\"msg-container\"]'));
    return msgs.length > 0 ? msgs[msgs.length-1].innerText : '';
  ")
  
  # Process with Hermes if new
  if [ "$LATEST_MSG" != "$LAST_PROCESSED" ]; then
    # Send to Hermes for processing
    HERMES_RESPONSE=$(hermes agentic "$LATEST_MSG")
    
    # Send response back via WhatsApp
    npx playwright-cli --session wa-session fill <message-input-ref> "$HERMES_RESPONSE"
    npx playwright-cli --session wa-session press Enter
    
    LAST_PROCESSED="$LATEST_MSG"
  fi
  
  sleep 30
done
```

## Security Considerations
- WhatsApp Web sessions grant full access to your WhatsApp account
- Store auth.json securely (consider encrypting if sensitive)
- Always logout from WhatsApp Web when using shared/computer
- Be aware that automated messaging may appear as bot-like behavior to contacts