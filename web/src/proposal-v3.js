import { versionLinks } from './proposal-v2.js?v=gen3-gate-1';
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function renderV3Shell(lang){
  const t=(zh,en)=>lang==='zh'?zh:en;
  return `<section id="solution" class="case-section"><p class="eyebrow">02 / PROPOSAL v3 · EDITORIAL REVISION</p><div class="section-head"><h2>${t('先核對需求與可比性，再做有界調查。','Confirm demand and comparability, then bound the investigation.')}</h2><span class="tag pending">${t('v3 複審已收到 · 補充另附','v3 re-review received · Supplement attached')}</span></div>${versionLinks(lang,'v3')}<p class="fine">${t('來源：Claude 對 v2 的外部審查 → 作者修訂。本方案沿用 Gen 2 計算，沒有新重跑；Gen 3 閘門另已實作、待實作外審。','Source: external Claude review of v2 → author revision. This proposal reuses Gen 2 calculations, with no new run. A separate Gen 3 gate is implemented and awaits code review.')}</p><div id="proposal-v3">${t('讀取方案 v3…','Loading proposal v3…')}</div></section>`;
}
export function renderV3Body(data,lang){
  const t=(zh,en)=>lang==='zh'?zh:en;
  const pick=pair=>escape(pair[lang==='zh'?0:1]);
  return data.sections.map(section=>`<h3>${pick(section.title)}</h3>${section.paragraphs.map(p=>`<p>${pick(p)}</p>`).join('')}`).join('')+`<div class="evidence-links"><a class="button primary" href="./evidence/f03/v3/proposal.md" download>${t('下載完整方案 v3','Download full proposal v3')} ↓</a><a class="text-link" href="./evidence/f03/v3/changes.md" target="_blank" rel="noopener noreferrer">${t('查看原修改理由','Read original revision reasons')} ↗</a><a class="text-link" href="./evidence/f03/v3/review-brief.md" download>${t('下載 v3 審查說明','Download v3 review brief')} ↓</a><a class="text-link" href="./evidence/f03/source-attribution.json" target="_blank" rel="noopener noreferrer">${t('核對方法來源','Check method provenance')} ↗</a><a class="text-link" href="./evidence/f03/v3-supplement-1.md" target="_blank" rel="noopener noreferrer">${t('閱讀 v3 小修補充','Read the v3 clarification supplement')} ↗</a></div><p class="fine">${t('完整原稿為中文；沒有新的現場成果或模型成本資料。v3 複審已收到，未發現改變方向缺陷，仍有小修；固定原文與新補充分開。設計審查不等於程式實作通過。','The full source proposal is in Chinese. There are no new operational results or model-cost records. v3 re-review has been received with minor clarifications and no direction-changing finding. The preserved source and supplement are separate. Design review does not validate the implementation.')}</p>`;
}
export async function attachProposalV3(lang){
  const host=document.querySelector('#proposal-v3');
  if(!host)return;
  try{
    const response=await fetch('./evidence/f03/v3/publication.json');
    if(!response.ok)throw Error('Unavailable');
    const data=await response.json();
    if(data.proposal_version!=='v3'||data.new_run!==false||data.gen3_implemented!==false)throw Error('Unexpected record');
    host.innerHTML=renderV3Body(data,lang);
  }catch{
    host.innerHTML=lang==='zh'?'<p>方案暫時無法載入，請<a href="./evidence/f03/v3/proposal.md">閱讀固定方案 v3</a>。</p>':'<p>Could not load the proposal. <a href="./evidence/f03/v3/proposal.md">Read preserved v3</a>.</p>';
  }
}
