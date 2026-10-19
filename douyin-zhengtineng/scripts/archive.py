#!/usr/bin/env python3
"""擷取已登入頁面實際回傳的作者作品，續傳下載並建立附章節的主題合輯。"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local'
INVENTORY = ROOT / 'data' / 'all-videos.json'
BROWSER = Path('/Users/chenzixuan/Library/Application Support/XinDouyinBot/work/browser/agent-browser')
FFMPEG = Path('/Applications/BlueStacks.app/Contents/MacOS/ffmpeg')
DEST = Path('/Volumes/未命名3/正体能影片整理')
PROFILE = 'https://www.douyin.com/user/MS4wLjABAAAAM1_p0rl5_KWjzfP8cs60YEcJxfmTdcnGPA0lIQzjFn4'
RULES = [
    ('01_評估與自我檢查', r'评估|测试|判断|辨别|自测'),
    ('02_呼吸與腹壓', r'呼吸|腹压|横膈|9090|90.?90|憋气'),
    ('03_骨盆旋轉與不對稱', r'骨盆.*旋|骨盆.*不对称|骨盆.*高低|长短腿|骨盆右|骨盆左|骶髂'),
    ('04_骨盆前後傾', r'骨盆前倾|骨盆后倾|前移|塌腰|反弓'),
    ('05_髖關節與臀部', r'髋|臀|梨状|内收肌|大腿后侧|腘绳'),
    ('06_膝蓋與腿型', r'膝|腿型|大小腿|[OXox]型|胫骨|股骨|股四头|大腿前侧'),
    ('07_足踝與步態', r'足|脚|踝|步态|走路|行走|步行'),
    ('08_肩頸與肩胛', r'肩|脖|颈|斜方|前锯|背阔|胸锁乳突|斜角肌'),
    ('09_胸廓與胸椎', r'胸|肋|后背|胸曲|上背'),
    ('10_脊椎與腰背', r'脊|腰|椎|侧弯|圆背|驼背'),
    ('11_核心與腹部', r'核心|腹直|腹斜|腹肌|腹横'),
    ('12_力量訓練與動作', r'深蹲|硬拉|卧推|推举|弯举|划船|大重量|力量|引体|增肌|分化|死肌肉|猛男体能'),
    ('13_放鬆熱身與活動度', r'泡沫轴|松解|放松|热身|拉伸|恢复|灵活|挤压|爬行|柔韧'),
    ('14_案例與回饋', r'反馈|案例|学员|前后对比'),
    ('17_營養飲食與身體組成', r'营养|蛋白|饮食|摄入|补剂|热量|食物|脂肪|体脂|GI|GL|胚型|身材|睾酮|铁元素|矿物质|钙|BMI|bmi|肌酸(?!胀|痛)|咖啡因'),
    ('18_睡眠情緒與神經', r'睡眠|多巴胺|内啡肽|焦虑|情绪|压力|神经'),
    ('19_不適與恢復觀念', r'疼痛|关节不适|损伤|乳酸'),
    ('20_創作者日常與交流', r'奇葩|评论区|提意见|大家.*意见|粉丝|体能挑战'),
    ('15_整體觀念', r'体态|功能|重心|代偿|训练|运动|纠正'),
]

def read(path, default):
    return json.loads(path.read_text()) if path.exists() else default

def write(path, value, private=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as handle:
        if private:
            os.fchmod(handle.fileno(), 0o600)
        json.dump(value, handle, ensure_ascii=False, indent=2)
    tmp.replace(path)

def browser(*args, timeout=45):
    p = subprocess.run([str(BROWSER), '--session', 'zhengtineng-archive', '--json', *args],
                       capture_output=True, text=True, timeout=timeout)
    data = json.loads(p.stdout)
    if not data.get('success'):
        raise RuntimeError(data.get('error', '瀏覽器命令失敗'))
    return data.get('data') or {}

def classify(title):
    tags = [name for name, pattern in RULES if re.search(pattern, title)]
    # 原標題比泛用hashtag優先，避免「營養增肌」因標籤被混入動作教學。
    subject=title.split('#',1)[0]
    direct=[name for name,pattern in RULES if re.search(pattern,subject)]
    priorities=['14_案例與回饋','17_營養飲食與身體組成','18_睡眠情緒與神經',
                '20_創作者日常與交流','03_骨盆旋轉與不對稱','04_骨盆前後傾',
                '05_髖關節與臀部','06_膝蓋與腿型','07_足踝與步態','08_肩頸與肩胛',
                '09_胸廓與胸椎','10_脊椎與腰背','11_核心與腹部','02_呼吸與腹壓',
                '01_評估與自我檢查','12_力量訓練與動作','13_放鬆熱身與活動度',
                '19_不適與恢復觀念','15_整體觀念']
    primary=next((name for name in priorities if name in direct),
                 next((name for name in priorities if name in tags),'16_待人工分類'))
    return primary, tags

def collect(max_rounds=130):
    PRIVATE.mkdir(exist_ok=True, mode=0o700)
    inventory = read(INVENTORY, {'author':'正体能', 'profile':PROFILE, 'expected_posts':939, 'videos':[], 'complete':False})
    entries = {v['id']:v for v in inventory['videos']}
    media = read(PRIVATE / 'media-urls.json', {})
    seen = set()
    stalled = 0
    ended = False
    for round_no in range(max_rounds):
        before = len(entries)
        requests = browser('network', 'requests', '--filter', '/aweme/v1/web/aweme/post/').get('requests', [])
        for request in requests:
            rid = request.get('requestId')
            if rid in seen or request.get('status') != 200:
                continue
            response = browser('network', 'request', rid)
            body = response.get('responseBody')
            if not body:
                continue
            body = json.loads(body)
            if body.get('status_code') != 0:
                continue
            seen.add(rid)
            for item in body.get('aweme_list', []):
                author = item.get('author') or {}
                if author.get('sec_uid') != PROFILE.rsplit('/', 1)[-1]:
                    continue
                ident = str(item['aweme_id'])
                title = item.get('desc', '')
                video = item.get('video') or {}
                group, tags = classify(title)
                images = item.get('images') or []
                entries[ident] = {'id':ident, 'title':title, 'url':f'https://www.douyin.com/video/{ident}',
                    'created':item.get('create_time'), 'date':dt.datetime.fromtimestamp(item['create_time'],dt.timezone(dt.timedelta(hours=8))).isoformat(),
                    'duration_ms':video.get('duration',item.get('duration',0)),
                    'width':video.get('width'), 'height':video.get('height'),
                    'type':'photo' if images else 'video', 'aweme_type':item.get('aweme_type'),
                    'category':group, 'tags':tags, 'classification_basis':'標題與標籤；尚未逐支內容審閱'}
                candidates = []
                for key in ('play_addr_h264','play_addr','play_addr_265'):
                    candidates.extend(video.get(key,{}).get('url_list',[]))
                candidates = list(dict.fromkeys(u for u in candidates if u.startswith('https://')))
                media[ident] = {'urls':candidates,'size':video.get('play_addr',{}).get('data_size',0)}
            if body.get('has_more') == 0 and body.get('aweme_list'):
                ended = True
        inventory.update(videos=sorted(entries.values(), key=lambda v:(v['created'],v['id'])),
                         complete=ended and len(entries)==inventory['expected_posts'],reached_end=ended,
                         checked_at=dt.datetime.now(dt.timezone.utc).isoformat())
        write(INVENTORY, inventory)
        write(PRIVATE / 'media-urls.json',media,private=True)
        print(f'清單輪次 {round_no+1}：{len(entries)}/939，讀至結尾={ended}',flush=True)
        if ended:
            break
        stalled = stalled+1 if len(entries)==before else 0
        if stalled >= 10:
            inventory['blocker']='連續10次捲動沒有新增作品，尚未確認全部作品。'
            write(INVENTORY,inventory)
            break
        browser('scroll','down','6500','--selector','div.route-scroll-container')
        time.sleep(1.5)
    return inventory

def safe_name(title):
    title = title.split('#',1)[0].strip() or '未命名'
    return re.sub(r'[\\/:*?"<>|\n\r]','_',title)[:65]

def probe(path, decode=False):
    args = [str(FFMPEG),'-hide_banner','-nostdin','-i',str(path)]
    p = subprocess.run(args,capture_output=True,text=True,timeout=60)
    text = p.stderr
    duration = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',text)
    if not duration or 'Video:' not in text:
        raise RuntimeError('影片格式或解碼檢查未通過')
    if decode:
        check=subprocess.run([str(FFMPEG),'-v','error','-nostdin','-i',str(path),'-t','1','-f','null','-'],capture_output=True,text=True,timeout=60)
        if check.returncode or check.stderr.strip():
            raise RuntimeError('影片開頭解碼檢查未通過')
    hours,minutes,seconds = map(float,duration.groups())
    return {'duration':hours*3600+minutes*60+seconds,'audio':'Audio:' in text,'bytes':path.stat().st_size}

def fetch_one(item, media, destination):
    ident = item['id']
    if item['type'] != 'video':
        return ident,{'status':'photo_not_video','title':item['title']}
    final = destination/'原始影片'/f'{ident}_{safe_name(item["title"])}.mp4'
    if final.exists():
        return ident,dict(status='downloaded',path=str(final),**probe(final))
    if shutil.disk_usage(destination).free < 10*1024**3:
        return ident,{'status':'failed','reason':'磁碟剩餘空間低於10GB，停止新增下載'}
    errors=[]
    for url in media.get(ident,{}).get('urls',[])[:6]:
        temporary=final.with_suffix('.mp4.part')
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.douyin.com/'})
            with urllib.request.urlopen(req,timeout=45) as response,temporary.open('wb') as handle:
                expected=int(response.headers.get('Content-Length',0))
                content_type=response.headers.get('Content-Type','')
                if not ('video' in content_type or 'octet-stream' in content_type):
                    raise RuntimeError('回傳非影片內容')
                shutil.copyfileobj(response,handle,1024*1024)
            if expected and temporary.stat().st_size != expected:
                raise RuntimeError('檔案長度不完整')
            info=probe(temporary,decode=True)
            claimed=item.get('duration_ms',0)/1000
            if claimed and abs(info['duration']-claimed)>max(3,claimed*.04):
                raise RuntimeError('下載片長與作品資料不一致')
            temporary.replace(final)
            return ident,dict(status='downloaded',path=str(final),**info)
        except Exception as exc:
            errors.append(type(exc).__name__+': '+str(exc).split('http')[0][:160])
            temporary.unlink(missing_ok=True)
    return ident,{'status':'failed','reason':'; '.join(errors) or '沒有可用下載網址'}

def check_destination(destination):
    if str(destination).startswith('/Volumes/'):
        volume=Path('/Volumes')/destination.parts[2]
        if not volume.is_mount():
            raise RuntimeError('指定的外接磁碟未掛載，停止處理。')

def download(destination, limit=0, workers=6):
    check_destination(destination)
    (destination/'原始影片').mkdir(parents=True,exist_ok=True)
    (destination/'處理紀錄').mkdir(parents=True,exist_ok=True)
    inventory=read(INVENTORY,{})
    media=read(PRIVATE/'media-urls.json',{})
    statefile=destination/'處理紀錄'/'download-state.json'
    state=read(statefile,{})
    entries=inventory.get('videos',[])
    pending=[v for v in entries if state.get(v['id'],{}).get('status') not in ('downloaded','photo_not_video')]
    if limit:
        pending=pending[:limit]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(fetch_one,v,media,destination) for v in pending]
        for future in concurrent.futures.as_completed(futures):
            ident,result=future.result()
            state[ident]=result
            write(statefile,state)
            print(f'{ident}：{result["status"]}，已下載 {sum(v.get("status")=="downloaded" for v in state.values())}/{len(entries)}',flush=True)
    write(destination/'處理紀錄'/'作品清單.json',inventory)
    return state

def ffescape(text):
    return text.replace('\\','\\\\').replace('=','\\=').replace(';','\\;').replace('#','\\#').replace('\n',' ')

def merge(destination,max_minutes=45,category=None):
    check_destination(destination)
    inventory=read(INVENTORY,{})
    state=read(destination/'處理紀錄'/'download-state.json',{})
    groups={}
    for item in inventory.get('videos',[]):
        status=state.get(item['id'],{})
        if status.get('status')=='downloaded':
            groups.setdefault(item['category'],[]).append((item,status))
    (destination/'分類合輯').mkdir(exist_ok=True)
    report=read(destination/'處理紀錄'/'merge-state.json',{})
    for group,rows in groups.items():
        if category and group!=category:
            continue
        batches=[[]]
        total=0
        for pair in rows:
            if total+pair[1]['duration']>max_minutes*60 and batches[-1]:
                batches.append([]);total=0
            batches[-1].append(pair);total+=pair[1]['duration']
        for number,batch in enumerate(batches,1):
            name=f'{group}_{number:02d}'
            signature=hashlib.sha256(json.dumps([(i['id'],s['bytes']) for i,s in batch]).encode()).hexdigest()
            final=destination/'分類合輯'/f'{name}.mp4'
            if final.exists() and report.get(name,{}).get('signature')==signature:
                continue
            if shutil.disk_usage(destination).free < 10*1024**3:
                raise RuntimeError('磁碟剩餘空間低於10GB，停止剪輯')
            temp=destination/'處理紀錄'/f'.{name}-segments'
            temp.mkdir(exist_ok=True)
            segments=[];chapters=[];offset=0;index=[]
            for order,(item,status) in enumerate(batch,1):
                segment=temp/f'{order:04d}.mp4'
                if segment.exists():
                    try:
                        existing=probe(segment)
                        if abs(existing['duration']-status['duration'])>max(2,status['duration']*.03):
                            segment.unlink()
                    except RuntimeError:
                        segment.unlink()
                if not segment.exists():
                    # 統一尺寸、幀率與聲音格式，保留直式畫面，橫式加留白。
                    vf='scale=720:1280:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30'
                    args=[str(FFMPEG),'-hide_banner','-loglevel','error','-nostdin','-y','-i',status['path']]
                    if not status['audio']:
                        args+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-shortest']
                    segment_partial=segment.with_suffix('.partial.mp4')
                    args+=['-map','0:v:0','-map','0:a:0' if status['audio'] else '1:a:0','-vf',vf,
                           '-c:v','h264_videotoolbox','-b:v','2500k','-pix_fmt','yuv420p',
                           '-c:a','aac','-b:a','128k','-ar','48000','-ac','2','-movflags','+faststart',str(segment_partial)]
                    p=subprocess.run(args,capture_output=True,text=True)
                    if p.returncode:
                        args[args.index('h264_videotoolbox')]='libx264'
                        bitrate=args.index('-b:v')
                        args[bitrate:bitrate+2]=['-crf','22','-preset','veryfast']
                        p=subprocess.run(args,capture_output=True,text=True)
                    if p.returncode:
                        raise RuntimeError('轉碼失敗：'+p.stderr[-400:])
                    probe(segment_partial)
                    segment_partial.replace(segment)
                length=probe(segment)['duration']
                start=round(offset*1000);end=round((offset+length)*1000)
                title=item['title'].split('#',1)[0].strip()
                chapters.append(f'[CHAPTER]\nTIMEBASE=1/1000\nSTART={start}\nEND={end}\ntitle={ffescape(title)}\n')
                index.append(f'{int(offset)//3600:02d}:{int(offset)//60%60:02d}:{int(offset)%60:02d}　{title}\n{item["url"]}')
                offset+=length;segments.append(segment)
                print(f'剪輯 {name}：{order}/{len(batch)}',flush=True)
            listing=temp/'concat.txt'
            listing.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in segments))
            metadata=temp/'chapters.ffmeta'
            metadata.write_text(';FFMETADATA1\ntitle='+ffescape(name)+'\ncomment=依標題分類；完整保留各原片，來源見同名索引。\n'+''.join(chapters))
            partial=final.with_suffix('.partial.mp4')
            args=[str(FFMPEG),'-hide_banner','-loglevel','error','-nostdin','-y','-f','concat','-safe','0','-i',str(listing),
                  '-i',str(metadata),'-map','0','-map_metadata','1','-map_chapters','1','-c','copy','-movflags','+faststart',str(partial)]
            subprocess.run(args,check=True,capture_output=True,text=True)
            info=probe(partial)
            if abs(info['duration']-offset)>max(3,len(batch)*.2):
                raise RuntimeError('合輯總片長不一致')
            verify=subprocess.run([str(FFMPEG),'-v','error','-nostdin','-i',str(partial),'-f','null','-'],capture_output=True,text=True)
            if verify.returncode or verify.stderr.strip():
                raise RuntimeError('合輯完整解碼檢查失敗：'+verify.stderr[-300:])
            partial.replace(final)
            final.with_suffix('.txt').write_text(name+'\n分類依據：標題與標籤，尚未逐支內容審閱。\n\n'+'\n\n'.join(index))
            report[name]={'signature':signature,'path':str(final),'count':len(batch),'ids':[i['id'] for i,s in batch],**info,'verified_full_decode':True}
            write(destination/'處理紀錄'/'merge-state.json',report)
            shutil.rmtree(temp)
            print(f'完成合輯 {name}：{len(batch)} 支，{offset/60:.1f} 分鐘，完整解碼通過',flush=True)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['collect','download','merge','status'])
    parser.add_argument('--destination',type=Path,default=DEST)
    parser.add_argument('--limit',type=int,default=0)
    parser.add_argument('--max-minutes',type=int,default=45)
    parser.add_argument('--category')
    parser.add_argument('--workers',type=int,default=6,choices=range(1,9))
    args=parser.parse_args()
    if args.action=='collect': collect()
    elif args.action=='download': download(args.destination,args.limit,args.workers)
    elif args.action=='merge': merge(args.destination,args.max_minutes,args.category)
    else:
        inventory=read(INVENTORY,{})
        downloads=read(args.destination/'處理紀錄'/'download-state.json',{})
        merges=read(args.destination/'處理紀錄'/'merge-state.json',{})
        print(json.dumps({'inventory':len(inventory.get('videos',[])),'complete':inventory.get('complete',False),
            'downloaded':sum(s.get('status')=='downloaded' for s in downloads.values()),
            'failed':sum(s.get('status')=='failed' for s in downloads.values()),
            'photos':sum(s.get('status')=='photo_not_video' for s in downloads.values()),'compilations':len(merges)},ensure_ascii=False))

if __name__=='__main__': main()
