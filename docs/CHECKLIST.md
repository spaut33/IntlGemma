# Pre-Launch Checklist

Before using TranslateGemma in production, verify:

## 🐳 Docker Setup

- [ ] Docker installed and running
- [ ] Docker Compose v2+ installed
- [ ] NVIDIA Container Toolkit installed
- [ ] GPU accessible from Docker: `docker run --rm --gpus all nvidia/cuda:13.0.0-base-ubuntu24.04 nvidia-smi`

## 📦 Build & Install

- [ ] Image built: `docker-compose build`
- [ ] CLI accessible: `./docker-run.sh --help`
- [ ] API starts: `docker-compose up -d api` (optional)

## 🧪 Test Run

- [ ] Languages list works: `./docker-run.sh languages`
- [ ] Check works: `./docker-run.sh check ./test_messages --all-languages`
- [ ] Translation works: `./docker-run.sh translate-missing ./test_messages -t ru`
- [ ] Backup created: `ls test_messages/*.bak`
- [ ] Results valid: `cat test_messages/ru.json`

## 📁 Your Project Setup

- [ ] Messages directory exists: `messages/`
- [ ] Source language file exists: `messages/en.json`
- [ ] Target language files exist: `messages/ru.json`, etc.
- [ ] Volume mounted in `docker-compose.yml`: `./messages:/app/messages`

## 🚀 Production Run

- [ ] Backup messages: `cp -r messages messages.backup`
- [ ] Check status: `./docker-run.sh check ./messages --all-languages`
- [ ] Translate: `./docker-run.sh translate-missing ./messages --all-languages`
- [ ] Verify: `./docker-run.sh check ./messages --all-languages`
- [ ] Review changes: `git diff messages/`

## 📊 Performance Tuning

- [ ] Batch size appropriate for GPU:
  - [ ] 8GB VRAM: `--batch-size 10-15`
  - [ ] 10GB+ VRAM: `--batch-size 20-30`
  - [ ] 16GB+ VRAM: `--batch-size 40-50`
- [ ] Monitor GPU usage: `docker-compose run --rm cli nvidia-smi`
- [ ] Adjust if OOM errors occur

## 📚 Documentation Review

- [ ] Read QUICKSTART.md
- [ ] Read DOCKER.md
- [ ] Review EXAMPLES.md for workflows
- [ ] Understand PROJECT_STRUCTURE.md (developers)

## 🔒 Security

- [ ] HuggingFace token secured (if using private models)
- [ ] Backups enabled (default: yes)
- [ ] Version control for translations
- [ ] `.env` file not committed (if created)

## ✅ Success Indicators

- [ ] Model loads without errors
- [ ] GPU detected and used
- [ ] Translations preserve nested structure
- [ ] ICU placeholders maintained
- [ ] Backup files created
- [ ] Progress bars displayed correctly
- [ ] Translation speed: 8-15 keys/sec (GPU)

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| GPU not detected | Install nvidia-container-toolkit |
| Out of memory | Reduce `--batch-size` |
| Slow performance | Increase `--batch-size` |
| Model download fails | Check internet, wait and retry |
| Permission errors | Add user to docker group |

## 📞 Getting Help

- Check DOCKER.md troubleshooting section
- Review EXAMPLES.md for similar use cases
- Check logs: `docker-compose logs -f`
- Verify GPU: `nvidia-smi`

---

**Ready to go?** Run: `make translate-missing`
