import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import esbuild from 'esbuild';
import { chromium } from 'playwright-core';

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '../../../..');
const frontend = path.join(repoRoot, 'mage_ai/frontend');
const outDir = path.join(here, 'dist');

const aliasRoots = {
  '@api': path.join(frontend, 'api'),
  '@components': path.join(frontend, 'components'),
  '@context': path.join(frontend, 'context'),
  '@interfaces': path.join(frontend, 'interfaces'),
  '@oracle': path.join(frontend, 'oracle'),
  '@storage': path.join(frontend, 'storage'),
  '@styles': path.join(frontend, 'styles'),
  '@utils': path.join(frontend, 'utils'),
  components: path.join(frontend, 'components'),
  utils: path.join(frontend, 'utils'),
};

function produceFixtures() {
  const python = spawnSync('python3', [path.join(here, 'produce_output.py')], {
    cwd: repoRoot,
    encoding: 'utf8',
    env: { ...process.env, PYTHONPATH: repoRoot, PYTHONWARNINGS: 'ignore' },
  });
  if (python.status !== 0) {
    process.stderr.write(python.stdout || '');
    process.stderr.write(python.stderr || '');
    throw new Error('produce_output.py failed');
  }
  return JSON.parse(python.stdout);
}

function resolveAlias(importPath) {
  if (importPath === '@api') {
    return path.join(frontend, 'api/index.ts');
  }
  const prefixes = Object.keys(aliasRoots).sort((a, b) => b.length - a.length);
  for (const prefix of prefixes) {
    if (importPath === prefix) {
      return aliasRoots[prefix];
    }
    if (importPath.startsWith(`${prefix}/`)) {
      return path.join(aliasRoots[prefix], importPath.slice(prefix.length + 1));
    }
  }
  return null;
}

const componentStub = `
function Stub() { return null; }
function useRouter() {
  return {
    asPath: '/',
    basePath: '',
    events: { off() {}, on() {} },
    pathname: '/',
    push() { return Promise.resolve(true); },
    query: {},
    replace() { return Promise.resolve(true); },
  };
}
module.exports = {
  __esModule: true,
  CSSTransition: Stub,
  CanvasRef: {},
  Col: Stub,
  CopyToClipboard: Stub,
  HTML5Backend: Stub,
  Image: Stub,
  Link: Stub,
  Row: Stub,
  default: Stub,
  dynamic() { return Stub; },
  media() { return ''; },
  parse() { return {}; },
  toast() {},
  useDrag() { return [{ isDragging: false }, function dragRef() {}]; },
  useDrop() { return [{ isOver: false }, function dropRef() {}]; },
  useRouter,
};
`;

const apiStub = `
function chain() {
  const fn = function apiStub() { return Promise.resolve({}); };
  return new Proxy(fn, {
    get() { return chain(); },
    apply() { return Promise.resolve({}); },
  });
}
const api = chain();
export default api;
`;

const stubbed = new Set([
  '@components/CodeBlock',
  '@components/CodeEditor',
  '@components/DependencyGraph',
  '@monaco-editor/react',
  'monaco-editor',
  'next/dynamic',
  'next/head',
  'next/image',
  'next/link',
  'next/router',
  'reaflow',
  'yaml',
]);

function packageInstalled(specifier) {
  const packageName = specifier.startsWith('@')
    ? specifier.split('/').slice(0, 2).join('/')
    : specifier.split('/')[0];
  return fs.existsSync(path.join(here, 'node_modules', packageName));
}

async function bundle() {
  fs.mkdirSync(outDir, { recursive: true });
  await esbuild.build({
    absWorkingDir: here,
    bundle: true,
    define: {
      'process.env.NODE_ENV': '"development"',
      'process.env.NEXT_PUBLIC_DEBUG': '"0"',
      'process.env.NEXT_PUBLIC_PRO': '""',
    },
    entryPoints: [path.join(here, 'harness.tsx')],
    format: 'iife',
    nodePaths: [path.join(here, 'node_modules')],
    jsx: 'automatic',
    loader: {
      '.css': 'empty',
      '.svg': 'dataurl',
    },
    outfile: path.join(outDir, 'harness.js'),
    platform: 'browser',
    plugins: [
      {
        name: 'mage-alias-and-stubs',
        setup(build) {
          build.onResolve({ filter: /.*/ }, (args) => {
            if (args.path === '@api') {
              return { path: path.join(here, 'stubs/api.js') };
            }
            if (args.path === 'path') {
              return { path: path.join(here, 'node_modules/path-browserify/index.js') };
            }
            if (stubbed.has(args.path)) {
              return { path: path.join(here, 'stubs/component.js') };
            }
            const resolved = resolveAlias(args.path);
            if (!resolved && !args.path.startsWith('.') && !args.path.startsWith('/') && !packageInstalled(args.path)) {
              return { path: path.join(here, 'stubs/component.js') };
            }
            if (!resolved) {
              return null;
            }
            const candidates = [
              resolved,
              `${resolved}.ts`,
              `${resolved}.tsx`,
              `${resolved}.js`,
              `${resolved}.jsx`,
              path.join(resolved, 'index.ts'),
              path.join(resolved, 'index.tsx'),
              path.join(resolved, 'index.js'),
            ];
            for (const candidate of candidates) {
              if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
                return { path: candidate };
              }
            }
            return { path: resolved };
          });
        },
      },
    ],
  });
}

function serve(fixtures) {
    const fixturesJson = JSON.stringify(fixtures).replace(/</g, '\\u003c');
    const htmlFor = (caseName) => `<!doctype html><html><body><div id="root"></div>
<script>window.global = window; window.process = window.process || { env: {} };</script>
<script>window.__case = ${JSON.stringify(caseName)}; window.__fixtures = ${fixturesJson};</script>
<script src="/harness.js"></script></body></html>`;
  const server = http.createServer((req, res) => {
    if (req.url === '/harness.js') {
      res.setHeader('content-type', 'text/javascript');
      res.end(fs.readFileSync(path.join(outDir, 'harness.js')));
      return;
    }
    const caseName = new URL(req.url, 'http://127.0.0.1').searchParams.get('case') || '';
    res.setHeader('content-type', 'text/html');
    res.end(htmlFor(caseName));
  });
  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({ port, server });
    });
  });
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function main() {
  fs.mkdirSync(path.join(here, 'stubs'), { recursive: true });
  fs.writeFileSync(path.join(here, 'stubs/component.js'), componentStub);
  fs.writeFileSync(path.join(here, 'stubs/api.js'), apiStub);

  const fixtures = produceFixtures();
  assert(fixtures.table_script.type === 'table', 'dataframe output was not stored as a table');
  assert(
    JSON.stringify(fixtures.table_script.sample_data.rows).includes('<script'),
    'format_output_data dropped the script markup before rendering',
  );
  assert(fixtures.kernel_html.type === 'text/html', 'kernel text/html was not preserved');

  await bundle();
  const { port, server } = await serve(fixtures);
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const cases = [
    'code-output-single-script',
    'code-output-single-handler',
    'code-output-list',
    'code-output-html-message',
    'renderer-html',
    'html-output',
    'table-output',
    'use-code-output',
    'cookie',
  ];
  const failures = [];
  try {
    for (const caseName of cases) {
      const page = await browser.newPage();
      const logs = [];
      page.on('pageerror', (error) => logs.push(error.message));
      try {
        await page.goto(`http://127.0.0.1:${port}/?case=${caseName}`, { waitUntil: 'domcontentloaded' });
        await page.waitForFunction(() => window.__renderDone === true, null, { timeout: 15000 });
        const result = await page.evaluate(() => ({
          cookieReadable: window.__cookieReadable,
          error: window.__renderError || '',
          xss: window.__mageXss || 0,
        }));
        if (result.error) {
          failures.push(`${caseName}: render failed: ${result.error}`);
        } else if (caseName === 'cookie') {
          if (result.cookieReadable !== false) {
            failures.push(`${caseName}: session cookie oauth_token is readable from page script after setToken`);
          }
        } else if (result.xss !== 0) {
          failures.push(`${caseName}: stored HTML executed in the page (count=${result.xss})`);
        }
        if (logs.length) {
          process.stderr.write(`${caseName} page errors: ${logs.join(' | ')}\n`);
        }
      } catch (error) {
        failures.push(`${caseName}: ${error.message}`);
        if (logs.length) {
          process.stderr.write(`${caseName} page errors: ${logs.join(' | ')}\n`);
        }
      } finally {
        await page.close();
      }
    }
  } finally {
    await browser.close();
    server.close();
  }
  if (failures.length) {
    throw new Error(failures.join('\n'));
  }
  process.stdout.write('stored html output did not execute and the session cookie was not readable\n');
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exit(1);
});
