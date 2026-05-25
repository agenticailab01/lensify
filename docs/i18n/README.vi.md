# ProjectLens

> Ống kính dự án thích ứng quét đơn + viên nang ngữ cảnh tối ưu hóa token cho bất kỳ codebase nào. Tiết kiệm 70-90% token định hướng cho các tác nhân mã hóa AI.

[English](../../README.md) · [Українська](README.uk.md) · **Tiếng Việt** · [Bahasa Indonesia](README.id.md)

## Là gì

ProjectLens là một plugin với **một lần quét** (50-150 ms) biến đổi bất kỳ codebase nào thành:

1. **`LENS.html`** — bản tóm tắt một trang mà con người đọc trong 30 giây
2. **`LENS.capsule.md`** — khối ngữ cảnh 800-3.600 token mà tác nhân AI của bạn tiếp nhận **thay vì** đọc 30+ tệp thô
3. **30 trình điều hợp framework** trên 8 gói hệ sinh thái (AI Apps, AI UIs, ML Core, Serving, Vector DB, Experiment, Enterprise, Notebooks)

## Cài đặt

Bốn kênh phân phối — chọn cái phù hợp với công cụ của bạn:

```bash
# Claude Code / Cowork — kéo và thả projectlens.plugin vào chat
# Cursor / VS Code Copilot / Codex / Gemini CLI — máy chủ MCP
git clone https://github.com/agenticailab01/projectlens ~/projectlens
# Aider / kịch bản / CI — CLI
pip install projectlens
# Bất kỳ công cụ nào đọc tệp ngữ cảnh — chế độ AGENTS.md
projectlens . --install-agents-md
```

## Tính năng chính

- **Độ sâu thích ứng** — tự động chọn T1 (Phác thảo) / T2 (Atlas) / T3 (La bàn)
- **30 trình điều hợp framework** — PyTorch, Transformers, LangChain, Pinecone, FastAPI, SQLAlchemy, Vue SFC, Docker Compose và nhiều hơn
- **5 hook phiên** (Claude Code) — loại bỏ trùng lặp đọc, theo dõi hoạt động, tiêm chọn lọc, nén đầu ra, bộ nhớ xuyên phiên
- **Bộ nén hội thoại** — `/projectlens compact` để thu hồi 8-25k token giữa phiên
- **Stdlib thuần** — không phụ thuộc runtime

## Kinh tế học token

| Giai đoạn | Tiết kiệm |
|---|---|
| Định hướng | **70-90%** |
| Đọc lại | **~25%** (phiên dài) |
| Tái tiêm theo prompt | **~60%** |
| Nén giữa phiên | **8-25k** token |

## Kiểm thử + Hiệu suất

527 bài kiểm thử đơn vị + 17 ngân sách hiệu suất/bảo mật được thực thi trong CI. Quét 500 tệp: **113 ms**.

## Giấy phép

MIT.
