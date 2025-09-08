import os, aiofiles, datetime
from app.infra.storage_supabase import upload_file
ART_DIR=os.environ.get('QIL_ART_DIR','artifacts')
async def run(vot,ctx):
    os.makedirs(ART_DIR,exist_ok=True)
    path=os.path.join(ART_DIR,f"day{int(vot['Day']):03d}_node_engineer.txt")
    async with aiofiles.open(path,'w') as fh:
        await fh.write('stub behavior output\n')
    url=upload_file(path)
    return {'files_created':1,'artifact_url':url}
