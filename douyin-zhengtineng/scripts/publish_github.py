#!/usr/bin/env python3
"""只上傳明確列出的公開索引與程式；排除影片、Cookie與簽名網址。"""
from pathlib import Path
import shutil
import subprocess
import archive

FILES=['README.md','index.html','data/catalog.json','data/all-videos.json','data/processing-status.json',
       'scripts/archive.py','scripts/library.py','scripts/finish_pipeline.py','scripts/publish_github.py']

def publish():
    checkout=archive.ROOT/'.local'/'publish'
    if not (checkout/'.git').is_dir():
        raise RuntimeError('請先將 susuyummy/web-crawlers clone 到 .local/publish。')
    def git(*args):
        return subprocess.run(['git',*args],cwd=checkout,check=True,capture_output=True,text=True).stdout
    remote=git('remote','get-url','origin').strip()
    if remote not in ('https://github.com/susuyummy/web-crawlers.git','https://github.com/susuyummy/web-crawlers'):
        raise RuntimeError('上傳目標不符，停止。')
    git('pull','--ff-only')
    for name in FILES:
        source=archive.ROOT/name
        if not source.is_file():
            continue
        target=checkout/'douyin-zhengtineng'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    git('add',*['douyin-zhengtineng/'+name for name in FILES if (archive.ROOT/name).is_file()])
    if git('diff','--cached','--name-only').strip():
        git('commit','-m','更新正体能影片分類、下載剪輯程式與實際處理進度')
        git('push','origin','HEAD:main')
    sha=git('rev-parse','HEAD').strip()
    print('GitHub 已更新：'+sha,flush=True)
    return sha

if __name__=='__main__':publish()
