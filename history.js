(function() {
    'use strict';

    var pathParts = window.location.pathname.replace(/\/$/, '').split('/');
    var dirname = pathParts[pathParts.length - 2] || '';
    var m = dirname.match(/^(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})$/);
    if (!m) {
        document.getElementById('archiveTimestamp').textContent = 'Invalid archive path';
        return;
    }

    var dateStr = m[1];
    var timeStr = m[2].replace('-', ':');
    var year = dateStr.slice(0, 4);
    var month = dateStr.slice(5, 7);
    var day = dateStr.slice(8, 10);

    document.getElementById('archiveTimestamp').textContent = dateStr + ' ' + timeStr;
    document.getElementById('archiveMeta').textContent = 'Loading...';

    var dataUrl = '../../../data/' + year + '/' + month + '/' + dateStr + '.json';

    fetch(dataUrl)
        .then(function(res) {
            if (!res.ok) throw new Error('Failed to load archive data: ' + res.status);
            return res.json();
        })
        .then(function(dayData) {
            var run = null;
            (dayData.runs || []).forEach(function(r) {
                if (r.time === timeStr) run = r;
            });
            if (!run) throw new Error('Run ' + timeStr + ' not found in ' + dateStr);

            document.getElementById('archiveMeta').textContent =
                run.categories.length + ' categories';

            renderNav(run.categories);
            renderContent(run.categories);
        })
        .catch(function(err) {
            document.getElementById('archiveMeta').textContent = err.message;
        });

    function renderNav(categories) {
        var nav = document.getElementById('archiveNav');
        categories.forEach(function(cat) {
            var a = document.createElement('a');
            a.href = '#' + cat.anchor;
            a.textContent = cat.name;
            a.addEventListener('click', function(e) {
                e.preventDefault();
                var target = document.getElementById(cat.anchor);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
            nav.appendChild(a);
        });
    }

    function renderContent(categories) {
        var main = document.getElementById('archiveContent');
        categories.forEach(function(cat) {
            var section = document.createElement('section');
            section.id = cat.anchor;
            section.className = 'category-section';

            var title = document.createElement('h2');
            title.className = 'category-title';
            title.textContent = cat.name;
            section.appendChild(title);

            if (cat.no_signal) {
                var ns = document.createElement('p');
                ns.className = 'no-signal';
                ns.textContent = 'No stories cleared the evidence gate this cycle.';
                section.appendChild(ns);
            }

            (cat.stories || []).forEach(function(story) {
                section.appendChild(renderStoryCard(story));
            });

            if ((cat.watchlist || []).length > 0) {
                section.appendChild(renderWatchlist(cat.watchlist));
            }

            main.appendChild(section);
        });
    }

    function renderStoryCard(story) {
        var card = document.createElement('div');
        card.className = 'story-card';

        var title = document.createElement('h4');
        title.textContent = story.title;
        card.appendChild(title);

        if (story.confidence !== null || story.heat !== null) {
            var scores = document.createElement('div');
            scores.className = 'story-scores';
            if (story.confidence !== null) {
                var conf = document.createElement('span');
                conf.className = 'story-score confidence';
                conf.textContent = 'confidence: ' + story.confidence;
                scores.appendChild(conf);
            }
            if (story.heat !== null) {
                var ht = document.createElement('span');
                ht.className = 'story-score heat';
                ht.textContent = 'heat: ' + story.heat;
                scores.appendChild(ht);
            }
            card.appendChild(scores);
        }

        if (story.fact_html) {
            var fact = document.createElement('div');
            fact.className = 'fact-block';
            fact.innerHTML = story.fact_html;
            card.appendChild(fact);
        }

        if (story.judgment_html) {
            var judgment = document.createElement('div');
            judgment.className = 'judgment-block';
            judgment.innerHTML = story.judgment_html;
            card.appendChild(judgment);
        }

        return card;
    }

    function renderWatchlist(items) {
        var wrapper = document.createElement('div');
        wrapper.className = 'watchlist-wrapper';

        var toggle = document.createElement('button');
        toggle.className = 'watchlist-toggle';
        toggle.setAttribute('aria-expanded', 'false');
        toggle.innerHTML = '<span class="arrow">\u25B6</span> ' + items.length + ' stories watching';

        var content = document.createElement('div');
        content.className = 'watchlist-content';

        var ul = document.createElement('ul');
        items.forEach(function(item) {
            var li = document.createElement('li');
            var a = document.createElement('a');
            a.href = item.url;
            a.target = '_blank';
            a.rel = 'noopener';
            a.textContent = item.title;
            li.appendChild(a);
            var meta = document.createElement('span');
            meta.className = 'watchlist-meta';
            meta.textContent = 'tier ' + item.tier + ' \u00b7 seen ' + item.seen_count;
            li.appendChild(meta);
            ul.appendChild(li);
        });
        content.appendChild(ul);
        wrapper.appendChild(toggle);
        wrapper.appendChild(content);

        toggle.addEventListener('click', function() {
            var isOpen = content.classList.toggle('open');
            toggle.classList.toggle('expanded', isOpen);
            toggle.setAttribute('aria-expanded', isOpen);
            toggle.innerHTML = '<span class="arrow">\u25B6</span> ' + (isOpen ? 'Hide' : (items.length + ' stories watching'));
        });

        return wrapper;
    }
})();
