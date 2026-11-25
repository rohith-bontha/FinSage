'use strict';

const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');

const ROOT = __dirname;
const DATA_DIR = path.join(ROOT, 'data');
const STORE = path.join(DATA_DIR, 'projects.json');
const HOST = process.env.HOST || '127.0.0.1';
const PORT = Number.parseInt(process.env.PORT || '3000', 10);
const MAX_BODY_BYTES = 2 * 1024 * 1024;
const MIME = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8', '.svg': 'image/svg+xml'
};

async function readProjects() {
  try {
    const content = await fs.readFile(STORE, 'utf8');
    const value = JSON.parse(content);
    return Array.isArray(value) ? value : [];
  } catch (error) {
    if (error.code === 'ENOENT') return [];
    throw error;
  }
}

async function writeProjects(projects) {
  await fs.mkdir(DATA_DIR, { recursive: true });
  const temp = `${STORE}.${process.pid}.tmp`;
  await fs.writeFile(temp, JSON.stringify(projects, null, 2), 'utf8');
  await fs.rename(temp, STORE);
}

function sendJson(res, status, value) {
  const body = JSON.stringify(value);
  res.writeHead(status, { 'Content-Type': MIME['.json'], 'Content-Length': Buffer.byteLength(body), 'Cache-Control': 'no-store' });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(Object.assign(new Error('Request body is too large.'), { status: 413 }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
      catch { reject(Object.assign(new Error('Request body must be valid JSON.'), { status: 400 })); }
    });
    req.on('error', reject);
  });
}

function validateSnapshot(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return 'A project snapshot is required.';
  const project = body.project;
  if (!project || typeof project !== 'object') return 'Project details are required.';
  if (typeof project.name !== 'string' || !project.name.trim() || project.name.length > 100) return 'Project name is required and must be at most 100 characters.';
  if (typeof project.domain !== 'string' || !project.domain.trim() || project.domain.length > 100) return 'A project use case is required.';
  if (typeof project.description !== 'string' || !project.description.trim() || project.description.length > 5000) return 'Project description is required and must be at most 5,000 characters.';
  if (!body.recommendation || typeof body.recommendation !== 'object') return 'An SDLC recommendation is required.';
  if (!Array.isArray(body.docs) || body.docs.length > 30) return 'A valid document list is required.';
  for (const doc of body.docs) {
    if (!doc || typeof doc.id !== 'string' || typeof doc.title !== 'string' || typeof doc.content !== 'string' || doc.content.length > 500000) {
      return 'Each document must include an ID, title, and content under 500,000 characters.';
    }
  }
  return null;
}

function safeRecord(snapshot, id, createdAt) {
  return {
    id,
    createdAt,
    updatedAt: new Date().toISOString(),
    project: snapshot.project,
    recommendation: snapshot.recommendation,
    docs: snapshot.docs
  };
}

async function handleApi(req, res, url) {
  if (req.method === 'GET' && url.pathname === '/api/health') {
    return sendJson(res, 200, { status: 'ok', service: 'finsage-local-api', storage: 'local-json' });
  }

  if (req.method === 'GET' && url.pathname === '/api/projects') {
    const projects = await readProjects();
    return sendJson(res, 200, projects.map(({ id, createdAt, updatedAt, project, recommendation }) => ({
      id, createdAt, updatedAt, name: project.name, domain: project.domain,
      recommendation: recommendation.primary
    })).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)));
  }

  if (url.pathname === '/api/projects' && req.method === 'POST') {
    const snapshot = await readBody(req);
    const issue = validateSnapshot(snapshot);
    if (issue) return sendJson(res, 400, { error: issue });
    const projects = await readProjects();
    const record = safeRecord(snapshot, crypto.randomUUID(), new Date().toISOString());
    projects.push(record);
    await writeProjects(projects);
    return sendJson(res, 201, record);
  }

  const match = url.pathname.match(/^\/api\/projects\/([0-9a-f-]{36})$/i);
  if (match && req.method === 'GET') {
    const record = (await readProjects()).find((item) => item.id === match[1]);
    return record ? sendJson(res, 200, record) : sendJson(res, 404, { error: 'Project not found.' });
  }

  if (match && req.method === 'PUT') {
    const snapshot = await readBody(req);
    const issue = validateSnapshot(snapshot);
    if (issue) return sendJson(res, 400, { error: issue });
    const projects = await readProjects();
    const index = projects.findIndex((item) => item.id === match[1]);
    if (index < 0) return sendJson(res, 404, { error: 'Project not found.' });
    projects[index] = safeRecord(snapshot, projects[index].id, projects[index].createdAt);
    await writeProjects(projects);
    return sendJson(res, 200, projects[index]);
  }

  return sendJson(res, 404, { error: 'API endpoint not found.' });
}

async function serveStatic(req, res, url) {
  let pathname;
  try { pathname = decodeURIComponent(url.pathname); }
  catch { res.writeHead(400); return res.end('Invalid path.'); }
  if (pathname === '/') pathname = '/index.html';
  const target = path.resolve(ROOT, `.${pathname}`);
  const relative = path.relative(ROOT, target);
  if (relative.startsWith('..') || path.isAbsolute(relative) || /(^|[\\/])(\.git|data|node_modules)([\\/]|$)/i.test(relative)) {
    res.writeHead(404); return res.end('Not found.');
  }
  let stat;
  try { stat = await fs.stat(target); }
  catch { res.writeHead(404); return res.end('Not found.'); }
  if (!stat.isFile()) { res.writeHead(404); return res.end('Not found.'); }
  const type = MIME[path.extname(target).toLowerCase()] || 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': type, 'Content-Length': stat.size, 'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'no-cache' });
  fs.createReadStream(target).pipe(res);
}

const server = http.createServer(async (req, res) => {
  let url;
  try { url = new URL(req.url, `http://${req.headers.host || `${HOST}:${PORT}`}`); }
  catch { return sendJson(res, 400, { error: 'Invalid request URL.' }); }
  try {
    if (url.pathname.startsWith('/api/')) await handleApi(req, res, url);
    else if (req.method === 'GET' || req.method === 'HEAD') await serveStatic(req, res, url);
    else sendJson(res, 405, { error: 'Method not allowed.' });
  } catch (error) {
    if (!res.headersSent) sendJson(res, error.status || 500, { error: error.status ? error.message : 'The server could not complete the request.' });
    else res.destroy();
    if (!error.status) console.error(error);
  }
});

server.listen(PORT, HOST, () => {
  console.log(`FinSage is running at http://${HOST}:${PORT}`);
  console.log(`Project API: http://${HOST}:${PORT}/api/health`);
});
