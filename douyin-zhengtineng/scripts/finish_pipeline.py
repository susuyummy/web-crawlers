#!/usr/bin/env python3
"""等待目前下載工作，續傳重試，建立所有主題合輯，再輸出完整性報告。"""
import argparse
import os
import time
import traceback
import archive
import library

def running(pid):
    try:
        os.kill(pid,0)
        return True
    except ProcessLookupError:
        return False

def run(wait_pid):
    archive.check_destination(archive.DEST)
    if wait_pid:
        while running(wait_pid):
            status=library.render()
            print(f'下載進度 {status["downloaded"]}/{status["videos"]}',flush=True)
            time.sleep(25)
    for attempt in range(3):
        status=library.render()
        if status['all_visible_videos_downloaded']:
            break
        print(f'續傳／重試第{attempt+1}輪',flush=True)
        archive.download(archive.DEST,workers=6)
    status=library.render()
    print('開始建立所有分類合輯',flush=True)
    inventory=archive.read(archive.INVENTORY,{})
    groups=sorted({v['category'] for v in inventory.get('videos',[]) if v['type']=='video'})
    errors={}
    for group in groups:
        try:
            archive.merge(archive.DEST,category=group)
        except Exception as exc:
            errors[group]=str(exc)
            print('合輯失敗，繼續其他主題：'+group+'；'+str(exc),flush=True)
        library.render()
    archive.write(archive.DEST/'處理紀錄'/'merge-errors.json',errors)
    status=library.render()
    archive.write(archive.DEST/'處理紀錄'/'pipeline-result.json',status)
    print('處理結束：'+str({k:status[k] for k in ['videos','downloaded','failed','compilations','merged_videos','all_visible_videos_merged']}),flush=True)
    import publish_github
    publish_github.publish()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait-pid',type=int,default=0)
    args=parser.parse_args()
    try:
        run(args.wait_pid)
    except Exception:
        traceback.print_exc()
        try:
            library.render()
        except Exception:
            pass
        raise
