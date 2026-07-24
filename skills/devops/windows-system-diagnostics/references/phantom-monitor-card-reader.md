# Phantom Monitor Card Reader — Worked Example

**Date:** 2026-07-07
**Trigger:** User reported "my harddrive doesnt work anymore"
**Machine:** SPIDEYMOON (Windows 10)

## Step-by-step walkthrough

### User setup
- C: = WD PC SN5000S SDEPNSJ-512G-1006 (NVMe SSD, 476 GB, 95% full)
- D: = Micron CT2000X9SSD9 (USB SSD, 1.9 TB, 63% full)
- Monitor = DisplayLink-6950 (VID_17E9, PID_4300) — USB-C monitor

### What the user saw
User thought C: or D: was dying. Actually both were Healthy.

### What was actually happening
System Event Log had 4x **Event 11 (disk):** "The driver detected a controller error on \Device\Harddisk2\DR11" — all at 5:10 PM the same day.

### Investigation steps that revealed the truth

1. **Physical disk health** — all healthy:
   ```
   Get-PhysicalDisk → all Healthy
   ```

2. **Drive-to-disk mapping** — mapped C:→Disk#0 (WD NVMe), D:→Disk#1 (Micron). Harddisk2 had no drive letter.

3. **Harddisk2 detail:**
   - Name: "Generic STORAGE DEVICE USB Device"
   - Index: 2
   - Interface: USB
   - Size: (empty — no media)
   - MediaType: (empty)
   - MediaLoaded: True (chipset is active, not a card)

4. **USB storage enumeration** revealed:
   - `I:\` — WPD "STORAGE DEVICE" (Generic brand) — same physical device as Harddisk2, exposed via portable device API
   - `Realtek USB CD-ROM` — Realtek chipset (VID_0BDA) showing as virtual CD-ROM
   - `Generic STORAGE DEVICE USB Device` — the actual disk class device
   - All from the same monitor's internal USB hub

5. **Full USB tree** confirmed:
   - **VID_17E9 PID_4300** = DisplayLink-6950 (the monitor)
   - **VID_0BDA PID_8151** = Realtek Mass Storage (built-in card reader inside the monitor)
   - **VID_05E3 PID_0751** = Genesys Logic Mass Storage (another card reader function)

### Conclusion
4 controller errors were from the **Realtek card reader chipset built into the USB-C DisplayLink monitor**. No card was inserted. The chipset's USB controller was just throwing errors — neither C: nor D: had any problems. Monitor had a minor USB hub glitch; no hardware was dying.

### Key tell
If you see **Realtek USB CD-ROM** alongside a **Generic STORAGE DEVICE** with no size, it's a monitor's built-in card reader. Always check the Size field — real drives report capacity; phantom devices don't.
