# Windows 灏忕櫧閰嶇疆鎸囧崡锛歁odelScope + ComfyUI + CapCut

> 閫傜敤鏈満锛歐indows 11锛宍<repo>`  
> 宸叉湁锛欳apCut 鍥介檯鐗堛€乄orkBuddy 鑷甫 Python 3.13銆丟it 2.56銆?NET csc銆丆apCut 鑷甫 ffmpeg  
> 鐩爣锛氬厛璺戦€氭湰鍦?ComfyUI锛屽啀鐢熸垚 30 绉掑窛鍛?Demo 鐨勫叧閿抚锛汼uno 鍜?Seedance 鏄簯绔湇鍔★紝涓嶅湪鏈湴瀹夎銆?
---

## 0. 鍏堟悶娓呮鍥涗釜涓滆タ

| 鍚嶇О | 鏄粈涔?| 瑕佷笉瑕佽 |
|---|---|---|
| **Python** | 杩愯 ComfyUI 鐨勮В閲婂櫒 | 鏈満宸叉湁 WorkBuddy Python 3.13锛涗篃鍙敤 Miniconda 瑁?3.11 |
| **Git** | 涓嬭浇 ComfyUI 婧愮爜鐨勫伐鍏?| 鏈満宸叉湁锛歚<Git>/git.exe` |
| **ComfyUI** | 鑺傜偣寮?AI 缁樺浘杞欢锛屼笉鏄?exe 瀹夎鍖咃紝鏄竴濂?Python 椤圭洰 | 闇€瑕佷笅杞?+ 瀹夎渚濊禆 |
| **ModelScope** | 闃块噷浜戞棗涓嬬殑 AI 妯″瀷绀惧尯锛岀被浼尖€滃浗鍐呯増 HuggingFace鈥?| 涓嶇敤瀹夎瀹㈡埛绔紝缃戦〉涓嬭浇鍗冲彲锛涗篃鍙 CLI |
| **Suno / Seedance** | 浜戠闊充箰 / 瑙嗛鐢熸垚鏈嶅姟 | 鏃犳硶鏈湴瀹夎锛岄渶瑕佽处鍙枫€侀搴︽垨 API Key |

**閲嶈锛?* Anaconda 5.3.1 鏄?2018 骞寸殑鑰佺増鏈紝榛樿 Python 3.6锛孋omfyUI 璺戜笉璧锋潵銆? 
濡傛灉鍙槸涓轰簡杩欎釜椤圭洰锛屽缓璁?*鍙栨秷/蹇界暐杩欎釜鏃?Anaconda**锛岀敤涓嬮潰鐨勬柟妗?A銆?
---

## 鏂规 A锛氭渶蹇窇閫氾紙鐢ㄦ湰鏈哄凡鏈夌殑 Python 3.13锛?
鎴戝凡缁忓湪鍚庡彴鐢?WorkBuddy 鐨?Python 寤轰簡铏氭嫙鐜锛?
```text
<repo>\env\comfy
```

### A1. 纭 Python 鑳界敤

鎵撳紑 PowerShell锛屽鍒讹細

```powershell
& "<repo>\env\comfy\Scripts\python.exe" --version
```

鐪嬪埌 `Python 3.13.14` 灏卞浜嗐€?
### A2. 瀹夎 CPU 鐗?PyTorch

> 浣犵殑鏄惧崱鏄?Quadro M2000M锛?GB 鏄惧瓨锛屽お鑰侊紝鍏堢敤 CPU 妯″紡鏈€绋炽€? 
> 鐢熸垚浼氭參锛屼絾鐜鑳借窇閫氾紱姝ｅ紡鍑虹墖鍐嶇敤 Seedance 浜戠銆?
```powershell
& "<repo>\env\comfy\Scripts\python.exe" -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
& "<repo>\env\comfy\Scripts\python.exe" -m pip install torch torchvision torchaudio -i https://mirrors.aliyun.com/pypi/simple/
```

楠岃瘉锛?
```powershell
& "<repo>\env\comfy\Scripts\python.exe" -c "import torch; print(torch.__version__)"
```

### A3. 涓嬭浇 ComfyUI

鏈満 Git 涓嶅湪 PATH锛岀洿鎺ョ敤瀹屾暣璺緞锛?
```powershell
& "<Git>/git.exe" clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git "<repo>\ComfyUI"
```

濡傛灉 GitHub 寰堟參锛屽彲浠ユ敼鐢ㄤ唬鐞嗗墠缂€锛?
```powershell
& "<Git>/git.exe" clone --depth 1 https://ghproxy.net/https://github.com/comfyanonymous/ComfyUI.git "<repo>\ComfyUI"
```

> 涓嶈鍙屽嚮 `main.py`銆侰omfyUI 瑕佺敤鍛戒护琛屽惎鍔ㄣ€?
### A4. 瀹夎 ComfyUI 渚濊禆

```powershell
cd "<repo>\ComfyUI"
& "<repo>\env\comfy\Scripts\python.exe" -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### A5. 鍚姩 ComfyUI

```powershell
cd "<repo>\ComfyUI"
& "<repo>\env\comfy\Scripts\python.exe" main.py --cpu
```

鐪嬪埌绫讳技锛?
```text
Starting server
To see the GUI go to: http://127.0.0.1:8188
```

灏辩敤娴忚鍣ㄦ墦寮€锛?
```text
http://127.0.0.1:8188
```

---

## 鏂规 B锛氭渶绋筹紙Miniconda + Python 3.11锛?
濡傛灉鏂规 A 鍦ㄥ畨瑁呬緷璧栨椂閬囧埌 Python 3.13 涓嶅吋瀹癸紝鍐嶇敤杩欎釜銆?
1. 涓嬭浇 Miniconda锛圵indows 64-bit锛夛細
   - 瀹樼綉锛歨ttps://docs.conda.io/en/latest/miniconda.html
   - 娓呭崕闀滃儚锛歨ttps://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/
2. 瀹夎鏃跺嬀閫夆€淎dd Miniconda3 to my PATH鈥濓紙灏忕櫧寤鸿鍕撅級銆?3. 鎵撳紑 **Anaconda Prompt**锛屾墽琛岋細

```powershell
conda create -n comfy python=3.11 -y
conda activate comfy
python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
python -m pip install torch torchvision torchaudio -i https://mirrors.aliyun.com/pypi/simple/
```

4. 鍚庨潰鐨?ComfyUI 涓嬭浇銆佷緷璧栧畨瑁呫€佸惎鍔ㄦ楠ゅ拰鏂规 A 涓€鏍凤紝鍙槸鎶?Python 璺緞鎹㈡垚锛?
```text
C:\Users\浣犵殑鐢ㄦ埛鍚峔miniconda3\envs\comfy\python.exe
```

---

## ModelScope 鏄粈涔堬紵鎬庝箞涓嬫ā鍨嬶紵

### 涓€鍙ヨ瘽

**ModelScope = 闃块噷鐨勬ā鍨嬩粨搴撱€?*  
ComfyUI 鍙槸鈥滅敾鍥捐蒋浠垛€濓紝鏈韩涓嶅甫妯″瀷锛涙ā鍨嬭鍘?ModelScope 鎴?HuggingFace 涓嬭浇锛屾斁鍒?ComfyUI 鐨?`models` 鏂囦欢澶归噷銆?
### 鏈€鎺ㄨ崘锛氱綉椤典笅杞斤紙灏忕櫧鏈€绋筹級

1. 鎵撳紑 ModelScope锛歨ttps://modelscope.cn
2. 鎼滅储 `stable-diffusion-v1-5`
3. 杩涘叆妯″瀷椤碉紝鐐广€屾ā鍨嬫枃浠躲€?4. 涓嬭浇杩欎釜鏂囦欢锛堢害 4GB锛夛細

```text
v1-5-pruned-emaonly.safetensors
```

5. 鎶婂畠鏀惧埌锛?
```text
<repo>\ComfyUI\models\checkpoints\v1-5-pruned-emaonly.safetensors
```

6. 鍥炲埌 ComfyUI 缃戦〉锛屽埛鏂帮紝鍦?`Load Checkpoint` 鑺傜偣閲岄€夋嫨瀹冦€?
> 濡傛灉缃戦〉涓嬭浇寰堟參锛岀敤 ModelScope 鐨?CLI锛堣涓嬶級銆?
### 鐢?ModelScope CLI 涓嬭浇锛堝畼鏂规帹鑽愶級

```powershell
& "<repo>\env\comfy\Scripts\python.exe" -m pip install modelscope -i https://mirrors.aliyun.com/pypi/simple/
```

鍙笅杩欎竴涓ā鍨嬫枃浠讹紝鐩存帴鏀捐繘 ComfyUI 鐨?checkpoints锛?
```powershell
& "<repo>\env\comfy\Scripts\python.exe" -m modelscope download `
  --model AI-ModelScope/stable-diffusion-v1-5 `
  v1-5-pruned-emaonly.safetensors `
  --local_dir "<repo>\ComfyUI\models\checkpoints"
```

鏈」鐩凡缁忕敤绛変环鐩撮摼涓嬭浇杩囧悓涓€涓枃浠讹紝骞舵牎楠岃繃 SHA256锛?
```text
鏂囦欢锛歷1-5-pruned-emaonly.safetensors
澶у皬锛?,265,146,304 bytes
SHA256锛?ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa
```

鏍￠獙缁撴灉涓?ModelScope 瀹樻柟鏂囦欢涓€鑷达紝**涓嶉渶瑕侀噸澶嶄笅杞?4GB**銆? 
濡傛灉浠ュ悗瑕侀噸涓嬶紝鍙互鐩存帴杩愯锛?
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<repo>\download_model_modelscope.ps1"
```

> ModelScope 鐨勬ā鍨?ID 鍙兘浼氬彉锛涗互缃戦〉涓婃樉绀虹殑涓哄噯銆? 
> 涓嬭浇妯″瀷涓嶉渶瑕佺櫥褰曪紝浣嗗ぇ鏂囦欢寤鸿鐧诲綍鍚庝笅杞斤紝閫熷害鏇寸ǔ銆? 
> `git lfs` 鍙湁鐢?Git 涓嬭浇妯″瀷鏃舵墠闇€瑕侊紱鐢?`modelscope download` 涓嶉渶瑕併€?
### ComfyUI 鐩綍閲屾ā鍨嬫斁鍝紵

```text
ComfyUI\
  models\
    checkpoints\      鈫?涓绘ā鍨嬶紙SD1.5 / SDXL锛?    vae\              鈫?VAE锛堟湁浜涙ā鍨嬭嚜甯︼紝涓嶇敤鍗曠嫭涓嬶級
    loras\            鈫?LoRA 椋庢牸/瑙掕壊
    controlnet\       鈫?濮挎€?绾跨鎺у埗
    ipadapter\        鈫?瑙掕壊涓€鑷存€э紙杩涢樁锛?```

**鏂版墜鍏堝彧鏀句竴涓?`checkpoints` 涓绘ā鍨嬶紝涓嶈涓€寮€濮嬭涓€鍫嗐€?*

---

## 绗竴娆℃墦寮€ ComfyUI 鎬庝箞娴嬭瘯锛?
1. 鍚姩鍚庢墦寮€ `http://127.0.0.1:8188`
2. 椤甸潰涓棿榛樿鏈変竴涓伐浣滄祦
3. 鍦?`Load Checkpoint` 鑺傜偣閫夋嫨 `v1-5-pruned-emaonly.safetensors`
4. 鍦ㄦ鍚戞彁绀鸿瘝閲岃緭鍏ワ細

```text
a rainy Sichuan teahouse at night, red lanterns, covered tea bowl, steam, flat vector illustration, cinematic, 16:9
```

5. 鐐广€孮ueue銆?銆岃繍琛屻€?6. CPU 浼氬緢鎱紝512脳512銆?0 姝ュ彲鑳借鍑犲垎閽燂紱鍏堢瓑涓€寮犲浘鍑烘潵锛岀‘璁ょ幆澧冮€氫簡

> 濡傛灉鎶ラ敊 `No module named ...`锛屾妸瀹屾暣鎶ラ敊鍙戠粰鎴戙€? 
> 濡傛灉鏄惧瓨/鍐呭瓨涓嶅锛屽厛闄嶅埌 512脳512銆?0 姝ャ€? 寮犲浘銆?
---

## Suno 鍜?Seedance 涓轰粈涔堜笉鑳借锛?
| 鏈嶅姟 | 鏈川 | 鏈湴鑳藉仛浠€涔?|
|---|---|---|
| **Suno** | 浜戠 AI 闊充箰 SaaS | 鍐欐瓕璇嶃€侀鏍兼彁绀鸿瘝锛涢渶瑕佽处鍙?棰濆害鎵嶈兘鐢熸垚 |
| **Seedance** | 鐏北鏂硅垷浜戠瑙嗛鐢熸垚 | 鍐欓暅澶存彁绀鸿瘝銆佸噯澶?API 鑴氭湰锛涢渶瑕?API Key/棰濆害 |

鎵€浠ユ垜缁欎綘鍑嗗鐨勬槸锛?
- `demo_sichuan/06_suno_prompt.md`锛氱洿鎺ュ鍒跺埌 Suno 鐨勬瓕璇?椋庢牸鎻愮ず璇?- `demo_sichuan/05_prompts/`锛?鈥? 涓?5 绉掗暅澶寸殑 ComfyUI / Seedance 鎻愮ず璇?- `demo_sichuan/tools/seedance_api.py`锛氭湁 Key 鎵嶆墽琛岀殑鍗犱綅鑴氭湰
- 鏈湴 Demo锛氬厛鐢?ComfyUI 鍏抽敭甯?+ ffmpeg 杩愬姩/杞満鍋氬彲鎾斁鐗堟湰

---

## 鍓槧鍥介檯鐗堬紙CapCut锛夋€庝箞鍙備笌锛?
浣犳湰鏈哄凡缁忚浜嗭細

```text
<CapCut>/CapCut.exe
<CapCut>/ffmpeg.exe
```

涓ゆ潯璺細

1. **鑷姩鍑虹墖锛堝綋鍓嶉」鐩敤锛?*锛氱敤 CapCut 鑷甫 ffmpeg 瀹屾垚鎷艰銆佸瓧骞曘€佽皟鑹层€丠.264/AAC 瀵煎嚭銆?2. **浜哄伐绮句慨锛堟帹鑽愪綘鏈€鍚庡仛锛?*锛氭妸鎴愮墖鎷栬繘 CapCut锛屽仛瀛楀箷鏍峰紡銆佽浆鍦恒€佽皟鑹层€佸搷搴︼紝鍐嶅鍑恒€?
鎴戣繕浼氱敓鎴愪竴涓?CapCut 鑽夌锛屾柟渚夸綘鐩存帴鎵撳紑缁х画鏀广€?
---

## 浣犵幇鍦ㄥ彧闇€瑕佸仛涓€浠朵簨

鍏堢‘璁よ繖涓懡浠よ兘璺戯細

```powershell
& "<repo>\env\comfy\Scripts\python.exe" --version
```

濡傛灉鑳界湅鍒?`Python 3.13.14`锛屽氨涓嶇敤绠?Anaconda 浜嗐€? 
濡傛灉鏃?Anaconda 杩樺湪瀹夎锛屽缓璁彇娑堬紱瀹冨お鑰侊紝涓嶉€傚悎 ComfyUI銆?
鎺ヤ笅鏉ョ殑瀹夎鎴戜細缁х画鍦ㄥ悗鍙板仛锛屼綘涓嶉渶瑕佹墜鍔ㄦ暡鍛戒护銆?
