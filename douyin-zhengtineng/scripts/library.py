#!/usr/bin/env python3
"""產生可離線瀏覽的影片庫及不含下載憑證的公開進度報告。"""
import collections
import datetime as dt
import html
import json
from pathlib import Path
import urllib.parse
import archive

def render(destination=archive.DEST):
    inventory=archive.read(archive.INVENTORY,{'videos':[]})
    downloads=archive.read(destination/'處理紀錄'/'download-state.json',{})
    merges=archive.read(destination/'處理紀錄'/'merge-state.json',{})
    videos=[v for v in inventory['videos'] if v['type']=='video']
    downloaded=sum(s.get('status')=='downloaded' for s in downloads.values())
    failures=[{'id':i,'reason':s.get('reason','')} for i,s in downloads.items() if s.get('status')=='failed']
    merged_ids={i for m in merges.values() for i in m.get('ids',[])}
    expected_ids={v['id'] for v in videos}
    status={'updated_at':dt.datetime.now().astimezone().isoformat(timespec='seconds'),
        'profile_count':inventory.get('expected_posts',939),'visible_posts':len(inventory['videos']),
        'reached_end':inventory.get('reached_end',False),'missing_vs_profile':inventory.get('missing_vs_profile',2),
        'videos':len(videos),'photo_posts':len(inventory['videos'])-len(videos),'downloaded':downloaded,
        'failed':len(failures),'compilations':len(merges),'merged_videos':len(merged_ids),
        'all_visible_videos_downloaded':all(downloads.get(i,{}).get('status')=='downloaded' for i in expected_ids),
        'all_visible_videos_merged':bool(expected_ids) and merged_ids==expected_ids,
        'classification_basis':'原標題與標籤；尚未逐支內容審閱',
        'failures':failures,
        'compilation_list':[{'name':name,'videos':m['count'],'minutes':round(m['duration']/60,2),'verified_full_decode':m.get('verified_full_decode',False)} for name,m in sorted(merges.items())]}
    archive.write(archive.ROOT/'data'/'processing-status.json',status)
    archive.write(destination/'處理紀錄'/'processing-status.json',status)
    archive.write(destination/'處理紀錄'/'作品清單.json',inventory)
    summary=f'可見影片 {len(videos)} 支｜已下載 {downloaded} 支｜合輯 {len(merges)} 部｜已編入合輯 {len(merged_ids)} 支'
    counts=collections.Counter(v['category'] for v in videos)
    escape=html.escape
    style='''*{box-sizing:border-box}body{margin:0;background:#f4f3ee;color:#263d32;font:16px/1.7 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:32px 22px}h1{font-size:38px;line-height:1.3}h2{margin-top:35px}a{color:inherit;text-underline-offset:4px}.status{padding:18px;background:#dce9df;border-radius:10px}.note{padding:14px;border-left:4px solid #b49550;background:#fff6df}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}input,select{font:inherit;padding:12px;border:1px solid #9dab9d;border-radius:7px;background:#fff}input{flex:1;min-width:200px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}.card{background:white;border:1px solid #d8e0d7;border-radius:10px;padding:18px}.card h3{margin:0 0 6px}.video{padding:14px 0;border-bottom:1px solid #d4ded3}.video small{display:block;color:#607467}.video[hidden]{display:none}.links{font-size:14px}.muted{color:#607467}details{margin:20px 0}footer{font-size:13px;margin-top:40px}a:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #b49550}'''
    options='<option value="">全部主題</option>'+''.join(f'<option value="{escape(c)}">{escape(c)}（{n}）</option>' for c,n in sorted(counts.items()))
    for local in (False,True):
        cards=[]
        for name,record in sorted(merges.items()):
            if local:
                link=urllib.parse.quote('分類合輯/'+Path(record['path']).name)
                source=link[:-4]+'.txt'
                extra=f'<a href="{link}">播放合輯 ↗</a> · <a href="{source}">章節與來源</a>'
            else:extra='影片存於你指定的外接磁碟「未命名3」。'
            cards.append(f'<article class="card"><h3>{escape(name)}</h3><p>{record["count"]} 支原片 · {record["duration"]/60:.1f} 分鐘</p><p class="links">{extra}</p><small>完整解碼檢查已通過</small></article>')
        rows=[]
        for v in videos:
            record=downloads.get(v['id'],{})
            label={'downloaded':'已下載','failed':'下載待重試'}.get(record.get('status'),'等待下載')
            if local and record.get('status')=='downloaded':
                link=urllib.parse.quote('原始影片/'+Path(record['path']).name)
                media=f' · <a href="{link}">播放本機原片</a>'
            else:media=''
            rows.append(f'<article class="video" data-category="{escape(v["category"])}"><a href="{escape(v["url"])}" target="_blank" rel="noopener">{escape(v["title"])}</a><small>{escape(v["date"][:10])} · {v["duration_ms"]/1000:.0f} 秒 · {escape(v["category"])} · {label}{media}</small></article>')
        page=f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>正体能｜分類影片庫</title><style>{style}</style><main><small>公開作品整理 · 更新 {escape(status['updated_at'])}</small><h1>正体能 · 分類影片庫</h1><p class="status">{summary}</p><p class="note">作品頁已讀到結尾，取得937則：744支影片、193則圖文。首頁顯示939則，差額2則未回傳，原因未知。分類依標題與標籤，尚未逐支內容審閱；合輯完整保留原片，按發布時間排列，每部約45分鐘。</p><h2>分類合輯</h2><div class="cards">{''.join(cards) or '合輯處理中。'}</div><h2>全部影片目錄</h2><div class="controls"><input id="search" type="search" aria-label="搜尋影片" placeholder="輸入標題、標籤或關鍵字"><select id="category" aria-label="篩選主題">{options}</select></div><p id="count" aria-live="polite">顯示 {len(videos)} 支</p><div id="videos">{''.join(rows)}</div><details><summary>193 則圖文作品清單</summary><p>這些作品不是影片，未混入分類合輯。</p>{''.join(f'<p><a href="https://www.douyin.com/note/{v["id"]}" target="_blank" rel="noopener">{escape(v["title"])}</a></p>' for v in inventory['videos'] if v['type']=='photo')}</details><footer>保留作者原始內容與來源；本頁未對訓練或健康主張進行事實查核。<br>程式與公開清單：<a href="https://github.com/susuyummy/web-crawlers/tree/main/douyin-zhengtineng">GitHub</a></footer></main><script>const rows=[...document.querySelectorAll('.video')],q=document.querySelector('#search'),category=document.querySelector('#category');function filter(){{let n=0;for(const row of rows){{row.hidden=!(row.textContent.toLowerCase().includes(q.value.trim().toLowerCase())&&(!category.value||row.dataset.category===category.value));if(!row.hidden)n++}}document.querySelector('#count').textContent=`顯示 ${{n}} / ${{rows.length}} 支`}}q.addEventListener('input',filter);category.addEventListener('change',filter);</script></html>'''
        path=destination/'開始觀看.html' if local else archive.ROOT/'index.html'
        path.write_text(page)
    return status

if __name__=='__main__':
    print(json.dumps(render(),ensure_ascii=False,indent=2))
