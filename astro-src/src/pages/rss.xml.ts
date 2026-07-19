import rss from '@astrojs/rss';
import { readSummaryMarkdown } from '../lib/data.ts';

function mdToHtml(md: string): string {
  let html = md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');
  html = html.replace(/^[-*] (.*$)/gm, '<li>$1</li>');
  html = html.replace(/(<li>[\s\S]*?<\/li>)(?!\s*<li>)/g, '<ul>$1</ul>');
  html = html.replace(/\n\n+/g, '</p><p>');
  html = `<p>${html}</p>`;
  return html;
}

export async function GET(context: { site?: URL }) {
  const base = 'https://firstsun-dev.github.io/news-getter/';
  const summary = readSummaryMarkdown();
  const rewritten = summary
    .replace(/\(\.\/history\//g, `(${base}history/`)
    .replace(/\.md\)/g, '.html)');
  const html = mdToHtml(rewritten);

  const titleMatch = /^# (.*)$/m.exec(summary);
  const entryTitle = titleMatch
    ? `AI News Intelligence Digest — ${titleMatch[1].replace(/[()]/g, '').trim()}`
    : 'AI News Intelligence Digest';

  return rss({
    title: 'AI News Intelligence Digest',
    description: 'Deep AI-summarized intelligence from global sources.',
    site: context.site ?? new URL(base),
    xmlns: { atom: 'http://www.w3.org/2005/Atom' },
    customData: `<language>zh-TW</language>`,
    items: [
      {
        title: entryTitle,
        link: base,
        pubDate: new Date(),
        description: 'Daily AI-summarized intelligence digest.',
        content: html,
      },
    ],
  });
}