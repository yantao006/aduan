(function () {
  const list = document.getElementById('graph-list');
  const search = document.getElementById('graph-search');
  const tabs = Array.from(document.querySelectorAll('.graph-tabs button'));
  if (!list || !search) return;

  const knownUrls = {
    '苹果': '/concept/苹果.html',
    '茅台': '/concept/茅台.html',
    '网易': '/concept/网易.html',
    '拼多多': '/concept/拼多多.html',
    '腾讯': '/company/tencent.html',
    'OPPO': '/company/oppo.html',
    'vivo': '/company/vivo.html',
    '步步高': '/company/bbk.html',
    '富国银行': '/company/wells-fargo.html',
    '巴菲特': '/person/buffett.html',
    '芒格': '/person/munger.html',
    '黄峥': '/person/huangzheng.html',
    '丁磊': '/person/dinglei.html',
    '陈明永': '/person/chenmingyong.html',
    '沈炜': '/person/shenwei.html',
    '金志江': '/person/jinzhijiang.html',
    '方三文': '/person/fangsanwen.html',
    '格雷厄姆': '/person/graham.html',
    '王石': '/person/wangshi.html',
    'Stop Doing List': '/concept/stop-doing-list.html',
  };

  const externalLinks = {
    '段永平': [['维基百科', 'https://zh.wikipedia.org/wiki/%E6%AE%B5%E6%B0%B8%E5%B9%B3']],
    '巴菲特': [['Wikipedia', 'https://en.wikipedia.org/wiki/Warren_Buffett']],
    '芒格': [['Wikipedia', 'https://en.wikipedia.org/wiki/Charlie_Munger']],
    '格雷厄姆': [['Wikipedia', 'https://en.wikipedia.org/wiki/Benjamin_Graham']],
    '王石': [['Wikipedia', 'https://en.wikipedia.org/wiki/Wang_Shi']],
    '黄峥': [['Wikipedia', 'https://en.wikipedia.org/wiki/Colin_Huang']],
    '丁磊': [['Wikipedia', 'https://en.wikipedia.org/wiki/Ding_Lei']],
    '苹果': [['官网', 'https://www.apple.com/'], ['投资者关系', 'https://investor.apple.com/']],
    '茅台': [['官网', 'https://www.moutaichina.com/']],
    '网易': [['官网', 'https://www.163.com/'], ['投资者关系', 'https://ir.netease.com/']],
    '拼多多': [['官网', 'https://www.pinduoduo.com/'], ['投资者关系', 'https://investor.pddholdings.com/']],
    '腾讯': [['官网', 'https://www.tencent.com/'], ['投资者关系', 'https://www.tencent.com/en-us/investors.html']],
    'OPPO': [['官网', 'https://www.oppo.com/']],
    'vivo': [['官网', 'https://www.vivo.com/']],
    '步步高': [['官网', 'https://www.gdbbk.com/']],
    '通用电气': [['官网', 'https://www.ge.com/'], ['投资者关系', 'https://www.ge.com/investor-relations']],
    'GE': [['官网', 'https://www.ge.com/'], ['投资者关系', 'https://www.ge.com/investor-relations']],
    '富国银行': [['官网', 'https://www.wellsfargo.com/'], ['投资者关系', 'https://www.wellsfargo.com/about/investor-relations/']],
  };

  const conceptNames = new Set([
    '买股票就是买公司', '未来现金流折现', '能力圈', '安全边际', '护城河', '长期持有',
    '集中投资', '不懂不做', '毛估估', '商业模式', '本分', '平常心', '不为清单',
    '企业文化', '消费者导向', '敢为天下后', '差异化', '焦点法则', '不做空',
    '不借钱', '好价格', '确定性', '持有等于买入', '犯错与纠错', '自由现金流',
    '便宜与贵', '管理层', '品牌', '复利', '贪婪恐惧', '市场先生', '收藏品', '10年视角',
    '企业文化与投资', '分红回购', '好生意好管理好价格', '价值投资'
  ]);

  const caseNames = new Set(['苹果', '茅台', '网易', '拼多多', '腾讯', 'OPPO', 'vivo', '步步高', '富国银行', '通用电气', 'GE']);

  function slugify(name) {
    const mapped = {
      'right business right people right price': 'right-business',
      '做对的事情': 'do-right',
      '把事情做对': 'do-right',
    };
    if (mapped[name]) return mapped[name];
    return name.toLowerCase()
      .replace(/[\/\s]+/g, '-')
      .replace(/[^\w\u4e00-\u9fff.-]+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }

  function nodeKind(node) {
    if (caseNames.has(node.id) || node.group === '投资案例') return 'case';
    if (node.type === 'concept' || conceptNames.has(node.id)) return 'concept';
    return 'entity';
  }

  function nodeUrl(id, kind) {
    if (knownUrls[id]) return knownUrls[id];
    if (kind === 'concept') return '/concept/' + slugify(id) + '.html';
    if (kind === 'case') return '/concept/' + slugify(id) + '.html';
    return null;
  }

  function render(nodes, adjacency, filter, query) {
    const q = query.trim().toLowerCase();
    const filtered = nodes
      .filter((node) => filter === 'all' || node.kind === filter)
      .filter((node) => !q || node.id.toLowerCase().includes(q))
      .slice(0, 36);

    list.innerHTML = filtered.map((node) => {
      const neighbors = (adjacency.get(node.id) || []).slice(0, 10);
      const tags = neighbors.map((edge) => {
        const kind = edge.node ? edge.node.kind : 'entity';
        const url = nodeUrl(edge.id, kind);
        const label = `${edge.id}<small>${edge.weight}</small>`;
        return url
          ? `<a class="graph-chip ${kind}" href="${url}">${label}</a>`
          : `<span class="graph-chip ${kind}">${label}</span>`;
      }).join('');
      const url = nodeUrl(node.id, node.kind);
      const title = url ? `<a href="${url}">${node.id}</a>` : node.id;
      const external = (externalLinks[node.id] || [])
        .map(([label, href]) => `<a class="external-source-link" href="${href}" target="_blank" rel="noopener">${label}</a>`)
        .join('');
      return `<article class="graph-card ${node.kind}">
        <div>
          <span>${node.group || node.kind}</span>
          <h2>${title}</h2>
          <p>${node.count || 0} 次共现</p>
          ${external ? `<div class="external-links graph-external"><span>外部资料</span>${external}</div>` : ''}
        </div>
        <div class="graph-neighbors">${tags}</div>
      </article>`;
    }).join('') || '<p class="empty-state">没有匹配结果。</p>';
  }

  fetch('knowledge-graph.json')
    .then((response) => response.json())
    .then((data) => {
      const nodes = data.nodes.map((node) => ({ ...node, kind: nodeKind(node) }))
        .sort((a, b) => (b.count || 0) - (a.count || 0));
      const byId = new Map(nodes.map((node) => [node.id, node]));
      const adjacency = new Map(nodes.map((node) => [node.id, []]));

      data.links.forEach((link) => {
        const source = typeof link.source === 'string' ? link.source : link.source.id;
        const target = typeof link.target === 'string' ? link.target : link.target.id;
        const weight = link.weight || link.value || 1;
        if (!adjacency.has(source) || !adjacency.has(target)) return;
        adjacency.get(source).push({ id: target, weight, node: byId.get(target) });
        adjacency.get(target).push({ id: source, weight, node: byId.get(source) });
      });

      adjacency.forEach((edges) => edges.sort((a, b) => b.weight - a.weight));

      let filter = 'all';
      const update = () => render(nodes, adjacency, filter, search.value);
      search.addEventListener('input', update);
      tabs.forEach((tab) => {
        tab.addEventListener('click', () => {
          tabs.forEach((item) => item.classList.remove('active'));
          tab.classList.add('active');
          filter = tab.dataset.filter;
          update();
        });
      });
      update();
    });
})();
