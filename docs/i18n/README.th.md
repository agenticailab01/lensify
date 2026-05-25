# ProjectLens

> เลนส์โปรเจกต์แบบปรับตัวได้ที่สแกนครั้งเดียว + แคปซูลบริบทที่เพิ่มประสิทธิภาพโทเค็นสำหรับโค้ดเบสใดๆ ประหยัดโทเค็นการปรับทิศทาง 70-90% สำหรับเอเจนต์การเขียนโค้ด AI

[English](../../README.md) · [Magyar](README.hu.md) · **ภาษาไทย** · [O'zbekcha](README.uz.md)

## คืออะไร

ProjectLens เป็นปลั๊กอินที่ **สแกนเพียงครั้งเดียว** (50-150 มิลลิวินาที) จะแปลงโค้ดเบสใดๆ เป็น:

1. **`LENS.html`** — สรุปหน้าเดียวที่มนุษย์อ่านได้ใน 30 วินาที
2. **`LENS.capsule.md`** — บล็อกบริบท 800-3,600 โทเค็นที่เอเจนต์ AI ของคุณดูดซับ **แทน** การอ่านไฟล์ดิบ 30+ ไฟล์
3. **อะแดปเตอร์เฟรมเวิร์ก 30 รายการ** ใน 8 แพ็กระบบนิเวศ (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## การติดตั้ง

```bash
# Claude Code / Cowork — ลาก projectlens.plugin เข้าไปในแชท
# Cursor / VS Code Copilot / Codex / Gemini CLI — เซิร์ฟเวอร์ MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / สคริปต์ / CI — CLI
pip install projectlens
# เครื่องมือใดๆ ที่อ่านไฟล์บริบท — โหมด AGENTS.md
projectlens . --install-agents-md
```

## คุณสมบัติหลัก

- **ความลึกแบบปรับตัวได้** (T1/T2/T3)
- **อะแดปเตอร์เฟรมเวิร์ก 30 รายการ** — PyTorch, LangChain, FastAPI, Pinecone, ฯลฯ
- **ฮุคเซสชัน 5 รายการ** (Claude Code)
- **เครื่องบดอัดการสนทนา** — กู้คืน 8-25k โทเค็นกลางเซสชัน
- **stdlib ล้วน** — ไม่มีการพึ่งพา runtime

## ใบอนุญาต

MIT.
