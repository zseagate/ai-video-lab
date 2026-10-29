# 鏈満鐜鐘舵€侊紙2026-10-22锛?
## 宸茬‘璁ゅ彲鐢?
| 缁勪欢 | 璺緞 / 鐗堟湰 | 鐘舵€?|
|---|---|---|
| Windows | Windows 11 浼佷笟鐗?LTSC 26100 | 鍙敤 |
| CPU | Intel Xeon E3-1535M v5锛? 鏍?8 绾跨▼ | 鍙敤 |
| 鍐呭瓨 | 绾?64 GB | 鍙敤 |
| GPU | NVIDIA Quadro M2000M锛?GB锛汭ntel HD P530 | 鍙敤浣嗗亸鑰?|
| Git | `<Git>/git.exe`锛?.56.0 | 鍙敤锛屾湭鍦?PATH |
| .NET csc | `<.NET>/csc.exe` | 鍙敤 |
| CapCut 鍥介檯鐗?| `<CapCut>/CapCut.exe`锛?.6.0.4097 | 宸插畨瑁?|
| CapCut ffmpeg | `<CapCut>/ffmpeg.exe` | 鍙敤 |
| WorkBuddy Python | `<WorkBuddy>/python.exe`锛?.13.14 | 鍙敤 |
| ComfyUI venv | `<repo>\env\comfy` | 宸插垱寤?|
| PyTorch | `2.14.1+cpu` | 宸插畨瑁?|
| ComfyUI 婧愮爜 | `<repo>\ComfyUI` | 宸?clone |
| SD1.5 妯″瀷 | `ComfyUI\models\checkpoints\v1-5-pruned-emaonly.safetensors`锛?,265,146,304 bytes | 宸蹭粠 ModelScope 涓嬭浇 |

## 姝ｅ湪瀹夎 / 寰呴獙璇?
| 缁勪欢 | 鐘舵€?|
|---|---|
| ComfyUI requirements | 宸插畨瑁呭畬鎴愶紙`transformers`銆乣av`銆乣comfy-kitchen`銆亀orkflow templates 绛夛級 |
| ComfyUI 鍚姩娴嬭瘯 | 宸查€氳繃锛沗http://127.0.0.1:8188` 杩斿洖 200 |
| ComfyUI 鍏抽敭甯х敓鎴?| 宸茶窇閫氾紱S01 娴嬭瘯鍥惧凡鐢熸垚锛孲D1.5 璐ㄩ噺涓€鑸紝闇€鎹㈡ā鍨嬫垨杩?Seedance |
| CapCut 鑽夌 | 宸茬敓鎴?`<CapCut Drafts>/Sichuan30`锛屽緟鎵撳紑楠岃瘉 |
| Anaconda 5.3.1 | 鐢ㄦ埛姝ｅ湪瀹夎锛涚増鏈お鏃э紙Python 3.6锛夛紝鏈」鐩笉浣跨敤 |

## 浜戠 / 鏃犳硶鏈湴瀹夎

| 鏈嶅姟 | 鍘熷洜 | 宸插噯澶?|
|---|---|---|
| Suno | 浜戠 SaaS锛岄渶瑕佽处鍙?棰濆害 | `demo_sichuan/06_suno_prompt.md` |
| Seedance | 鐏北鏂硅垷浜戠锛岄渶瑕?API Key/棰濆害 | `demo_sichuan/07_seedance_api.md` + `tools/seedance_api.py` |
| 鍓槧鑷姩绮楀壀 Skill | 鏈畨瑁?GUI 鑷姩鍖?| 鍏堢敤 CapCut 鑽夌 + 鑷甫 ffmpeg锛屼汉宸ョ簿淇?|

## 宸插畬鎴愭垚鐗?
| 椤圭洰 | 鍊?|
|---|---|
| 鏂囦欢 | `demo_sichuan/output/sichuan_teahouse_16x9_v01.mp4` |
| 鏃堕暱 | 30.00 绉?|
| 鍒嗚鲸鐜?| 1280脳720 |
| 甯х巼 | 30fps |
| 瑙嗛 | H.264 |
| 闊抽 | AAC 44.1kHz 绔嬩綋澹?|
| 澶у皬 | 绾?14.6 MB |
| 鍐呭 | 鍘熷垱宸濆懗鍙樹綋銆婁竴纰楄尪锛屾參鎱㈡憜銆?|
| 鏄庣‘閬垮紑 | 鐔婄尗 Rap 鏈綋銆佸師妗堜緥瑙掕壊/姝岃瘝/鍝佺墝/娲诲姩鏍囪瘑 |

## 閲嶈璺緞

```text
椤圭洰鏍圭洰褰?       <repo>
鏂?Demo           <repo>\demo_sichuan
ComfyUI           <repo>\ComfyUI
ComfyUI venv      <repo>\env\comfy
妯″瀷              <repo>\ComfyUI\models\checkpoints
CapCut 鑽夌       <CapCut Drafts>/Sichuan30
瀹夎鎸囧崡          <repo>\SETUP_WINDOWS.md
```

## 涓嬩竴姝?
1. 娉ㄥ唽鍗虫ⅵ缃戦〉鐗堬紝棰嗗彇姣忔棩绉垎銆?2. 鐢?Doubao-Seed-Evolving 鍐欒瘝 / 鍐欏垎闀?/ 鍐欐彁绀鸿瘝銆?3. 鐢?Suno 鍑?1鈥? 棣?30 绉掑唴鍊欓€夋瓕銆?4. 鍦ㄥ嵆姊︾敓鎴?S01鈥揝05锛? 绉掗暅澶达紱棰濆害涓嶅鏃剁浜屽ぉ琛ラ暅鎴栬蛋鍥剧敓瑙嗛銆?5. 鍦?CapCut 鑽夌閲屽仛鏈€鍚庡瓧骞曘€佽皟鑹层€佸搷搴︼紝瀵煎嚭銆?6. ComfyUI 缁х画淇濈暀涓烘湰鍦扮粌涔犮€侀甯у浘鐢熸垚鍜屽鐢ㄥ厹搴曘€?7. 鍙戝竷鍓嶅啀鍋氬叕寮€/绉佹湁鎷嗗垎鍜屾晱鎰熶俊鎭壂鎻忥紱鏈‘璁ゅ墠涓?push銆?
