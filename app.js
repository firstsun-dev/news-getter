(function() {
    'use strict';

    var contentEl = document.getElementById('content');
    var navEl = document.getElementById('categoryNav');
    var historyEl = document.getElementById('history');
    var footerEl = document.getElementById('footer');

    function h(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function renderSite(data) {
        renderMeta(data.meta);
        renderNav(data.categories);
        renderContent(data.categories);
        renderFooter(data.meta);
        initScrollSpy();
    }

    function renderMeta(meta) {
        document.getElementById('briefTimestamp').textContent = meta.timestamp;
        document.getElementById('statDeep').textContent = meta.deep_count + ' deep analyses';
        document.getElementById('statWatch').textContent = meta.watch_count + ' stories tracked';
        document.getElementById('statCats').textContent = meta.cat_count + ' categories';
    }

    function renderNav(categories) {
        var inner = navEl.querySelector('.category-nav-inner');
        categories.forEach(function(cat) {
            var a = document.createElement('a');
            a.href = '#' + cat.anchor;
            a.className = 'cat-nav-link';
            a.textContent = cat.name;
            a.addEventListener('click', function(e) {
                e.preventDefault();
                var target = document.getElementById(cat.anchor);
                if (target) {
                    var navHeight = navEl.offsetHeight;
                    var top = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
                    window.scrollTo({ top: top, behavior: 'smooth' });
                }
            });
            inner.appendChild(a);
        });
    }

    function renderContent(categories) {
        categories.forEach(function(cat) {
            var section = document.createElement('section');
            section.id = cat.anchor;
            section.className = 'category-section';

            var title = document.createElement('h2');
            title.className = 'category-title';
            title.textContent = cat.name;
            section.appendChild(title);

            if (cat.archive_url) {
                var archiveLink = document.createElement('a');
                archiveLink.href = cat.archive_url;
                archiveLink.className = 'archive-link';
                archiveLink.textContent = 'Full archive \u2192';
                section.appendChild(archiveLink);
            }

            if (cat.no_signal) {
                var ns = document.createElement('p');
                ns.className = 'no-signal';
                ns.textContent = 'No stories cleared the evidence gate this cycle.';
                section.appendChild(ns);
            }

            cat.stories.forEach(function(story) {
                section.appendChild(renderStoryCard(story));
            });

            if (cat.watchlist.length > 0) {
                section.appendChild(renderWatchlist(cat.watchlist));
            }

            contentEl.appendChild(section);
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

    function renderHistory(historyData) {
        historyData.forEach(function(day) {
            var dayDiv = document.createElement('div');
            dayDiv.className = 'timeline-day';

            var dateDiv = document.createElement('div');
            dateDiv.className = 'timeline-date';
            dateDiv.textContent = day.date;
            dayDiv.appendChild(dateDiv);

            day.runs.forEach(function(run) {
                var runDiv = document.createElement('div');
                runDiv.className = 'timeline-run';

                var timeEl = document.createElement('time');
                timeEl.textContent = run.time;
                runDiv.appendChild(timeEl);

                var chipsDiv = document.createElement('span');
                chipsDiv.className = 'timeline-chips';
                var timePath = run.time.replace(':', '-');
                run.categories.forEach(function(catName) {
                    var a = document.createElement('a');
                    a.href = 'history/' + day.date + '_' + timePath + '/index.html#' + catName.replace(/ /g, '-');
                    a.textContent = catName;
                    chipsDiv.appendChild(a);
                });
                runDiv.appendChild(chipsDiv);
                dayDiv.appendChild(runDiv);
            });

            historyEl.appendChild(dayDiv);
        });
    }

    function renderFooter(meta) {
        footerEl.textContent = 'AI Intelligence Pipeline \u00b7 Updated ' + meta.generated;
    }

    function initScrollSpy() {
        var links = navEl.querySelectorAll('.cat-nav-link');
        var sections = document.querySelectorAll('.category-section');

        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                var id = entry.target.getAttribute('id');
                var link = navEl.querySelector('a[href="#' + id + '"]');
                if (link) {
                    if (entry.isIntersecting) {
                        links.forEach(function(l) { l.classList.remove('active'); });
                        link.classList.add('active');
                    }
                }
            });
        }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 });

        sections.forEach(function(s) { observer.observe(s); });
    }

    fetch('data/site_data.json')
        .then(function(res) {
            if (!res.ok) throw new Error('Failed to load data: ' + res.status);
            return res.json();
        })
        .then(renderSite)
        .catch(function(err) {
            contentEl.innerHTML = '<p class="no-signal">Unable to load briefing data. ' + h(err.message) + '</p>';
        });

    fetch('data/history_index.json')
        .then(function(res) {
            if (!res.ok) throw new Error('Failed to load history: ' + res.status);
            return res.json();
        })
        .then(renderHistory)
        .catch(function(err) {
            historyEl.innerHTML = '<p class="no-signal">Unable to load archive. ' + h(err.message) + '</p>';
        });
})();
