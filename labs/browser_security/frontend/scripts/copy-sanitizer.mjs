// The Django fixture embeds this pinned UMD artifact with a fresh nonce.
// Copy after Vite empties dist, retaining the upstream license alongside it.
import { copyFile, readFile } from 'node:fs/promises'

const project = new URL('../', import.meta.url)
const packageRoot = new URL('node_modules/dompurify/', project)
const metadata = JSON.parse(await readFile(new URL('package.json', packageRoot), 'utf8'))
const configured = JSON.parse(await readFile(new URL('package.json', project), 'utf8'))
if (metadata.version !== configured.dependencies.dompurify) throw new Error('Install the exact pinned DOMPurify dependency before building.')
const source = await readFile(new URL('dist/purify.min.js', packageRoot), 'utf8')
if (source.length > 200000 || /<\/script/i.test(source)) throw new Error('Review sanitizer asset before embedding this release in a script element.')
await copyFile(new URL('dist/purify.min.js', packageRoot), new URL('dist/trusted-sanitizer.js', project))
await copyFile(new URL('LICENSE', packageRoot), new URL('dist/trusted-sanitizer-LICENSE.txt', project))
console.log(`Copied DOMPurify ${metadata.version} for the fixed Trusted Types frame.`)
