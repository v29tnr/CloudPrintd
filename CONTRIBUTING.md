# CloudPrintd Development Guide

## Project Structure

```
PrinterServer/
├── app/                        # FastAPI application
│   ├── __init__.py
│   ├── main.py                # Main FastAPI app & routes
│   ├── models.py              # Pydantic models
│   ├── config.py              # Configuration manager
│   ├── security.py            # Authentication & security
│   └── printer.py             # Printer communication
├── update_manager/            # Update management system
│   ├── __init__.py
│   └── manager.py             # UpdateManager class
├── webui/                     # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── api.js            # API client
│   │   ├── App.jsx           # Main app component
│   │   └── main.jsx          # Entry point
│   ├── package.json
│   └── vite.config.js
├── config/                    # Configuration files
│   ├── defaults.json
│   ├── printers.defaults.json
│   └── update.json
├── hooks/                     # Lifecycle hooks
│   ├── pre-install.sh
│   ├── post-install.sh
│   ├── pre-upgrade.sh
│   ├── post-upgrade.sh
│   └── rollback.sh
├── docs/                      # Documentation
│   ├── setup-guide.md
│   ├── api-integration.md
│   ├── troubleshooting.md
│   └── update-management.md
├── requirements.txt           # Python dependencies
├── build-release.sh          # Build script
├── CloudPrintd.service       # Systemd service
├── CHANGELOG.md
└── README.md
```

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Local Development

1. Clone repository:
```bash
git clone https://github.com/yourorg/CloudPrintd.git
cd CloudPrintd
```

2. Set up Python environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up frontend:
```bash
cd webui
npm install
cd ..
```

4. Run backend:
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. Run frontend (in separate terminal):
```bash
cd webui
npm run dev
```

6. Access:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Use async/await for I/O operations
- Maximum line length: 100 characters

### JavaScript/React
- Use functional components
- Follow Airbnb React style guide
- Use async/await over promises
- Use meaningful variable names
- Add PropTypes or TypeScript

## Testing

### Python Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

### Frontend Tests
```bash
cd webui
npm test
```

## Building

### Development Build
```bash
# Backend - no build needed (interpreted)

# Frontend
cd webui
npm run build
```

### Production Release
```bash
# Build everything and create package
./build-release.sh 1.0.0 stable
```

## Contributing

### Branching Strategy
- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `release/*` - Release preparation

### Commit Messages
Follow conventional commits:
- `feat: Add new feature`
- `fix: Fix bug`
- `docs: Update documentation`
- `style: Code style changes`
- `refactor: Code refactoring`
- `test: Add tests`
- `chore: Maintenance tasks`

### Pull Request Process
1. Create feature branch from `develop`
2. Make changes with tests
3. Update documentation
4. Submit PR to `develop`
5. Code review
6. Merge after approval

## Release Process

1. Update version in:
   - `app/main.py` (app version)
   - `webui/package.json`
   - `CHANGELOG.md`

2. Create release branch:
```bash
git checkout -b release/1.0.0 develop
```

3. Build release:
```bash
./build-release.sh 1.0.0 stable
```

4. Test package on Raspberry Pi

5. Merge to main and tag:
```bash
git checkout main
git merge release/1.0.0
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin main --tags
```

6. Create GitHub release with package

7. Update update server manifest

## Debugging

### Backend
```python
# Add to main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Frontend
```javascript
// Use React DevTools
// Add console.log statements
console.log('Debug:', data);
```

### Network Issues
```bash
# Test printer connectivity
nc -zv 192.168.1.100 9100

# Test API
curl -v http://localhost:8000/api/v1/health
```

## Performance Optimization

### Backend
- Use async for I/O operations
- Implement connection pooling
- Cache printer status
- Batch operations where possible

### Frontend
- Code splitting
- Lazy loading components
- Minimise API calls
- Use React.memo for expensive components

## Security Best Practices

- Never commit secrets to Git
- Use environment variables for sensitive data
- Validate all user input
- Use parameterised queries (if using DB)
- Implement rate limiting
- Keep dependencies updated
- Use HTTPS in production
- Implement CORS appropriately

## Deployment

See [Setup Guide](docs/setup-guide.md) for deployment instructions.

## License

MIT License - See LICENSE file

## Support

- GitHub Issues: https://github.com/yourorg/CloudPrintd/issues
- Documentation: https://docs.CloudPrintd.local
- Email: support@CloudPrintd.local
