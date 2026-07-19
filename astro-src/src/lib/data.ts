import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const repoRoot = resolve(process.cwd(), '..');

export interface StorySummary {
  title: string;
  confidence: number | null;
  heat: number | null;
  fact_html: string;
  judgment_html: string;
}

export interface WatchlistItem {
  title: string;
  url: string;
  tier: number;
  seen_count: number;
}

export interface CategoryData {
  name: string;
  anchor: string;
  archive_url: string | null;
  stories: StorySummary[];
  watchlist: WatchlistItem[];
  no_signal: boolean;
  deep_count: number;
  watch_count: number;
}

export interface SiteMeta {
  timestamp: string;
  generated: string;
  deep_count: number;
  watch_count: number;
  cat_count: number;
}

export interface SiteData {
  meta: SiteMeta;
  categories: CategoryData[];
}

export interface RunSummary {
  time: string;
  categories: string[];
}

export interface DayIndex {
  date: string;
  runs: RunSummary[];
}

export interface DayData {
  date: string;
  runs: {
    time: string;
    categories: CategoryData[];
  }[];
}

export function loadSiteData(): SiteData {
  const raw = readFileSync(resolve(repoRoot, 'data/site_data.json'), 'utf-8');
  return JSON.parse(raw) as SiteData;
}

export function loadHistoryIndex(): DayIndex[] {
  const raw = readFileSync(resolve(repoRoot, 'data/history_index.json'), 'utf-8');
  return JSON.parse(raw) as DayIndex[];
}

export function loadDayJson(date: string): DayData {
  const [y, m] = date.split('-');
  const raw = readFileSync(
    resolve(repoRoot, 'data', y, m, `${date}.json`),
    'utf-8',
  );
  return JSON.parse(raw) as DayData;
}

export function readSummaryMarkdown(): string {
  return readFileSync(resolve(repoRoot, 'summary.md'), 'utf-8');
}