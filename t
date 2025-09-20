[0;1;32m●[0m ollama.service - Ollama Service
     Loaded: loaded (]8;;file://raspberrypi/etc/systemd/system/ollama.service/etc/systemd/system/ollama.service]8;;; [0;1;32menabled[0m; preset: [0;1;32menabled[0m)
     Active: [0;1;32mactive (running)[0m since Fri 2025-09-19 10:07:00 EDT; 16min ago
   Main PID: 840 (ollama)
      Tasks: 8[0;38;5;245m (limit: 8750)[0m
        CPU: 205ms
     CGroup: /system.slice/ollama.service
             └─[0;38;5;245m840 /usr/local/bin/ollama serve[0m

Sep 19 10:07:00 raspberrypi systemd[1]: Started ollama.service - Ollama Service.
Sep 19 10:07:00 raspberrypi ollama[840]: time=2025-09-19T10:07:00.910-04:00 level=INFO source=routes.go:1332 msg="server config" env="map[CUDA_VISIBLE_DEVICES: GPU_DEVICE_ORDINAL: HIP_VISIBLE_DEVICES: HSA_OVERRIDE_GFX_VERSION: HTTPS_PROXY: HTTP_PROXY: NO_PROXY: OLLAMA_CONTEXT_LENGTH:4096 OLLAMA_DEBUG:INFO OLLAMA_FLASH_ATTENTION:false OLLAMA_GPU_OVERHEAD:0 OLLAMA_HOST:http://127.0.0.1:11434 OLLAMA_INTEL_GPU:false OLLAMA_KEEP_ALIVE:5m0s OLLAMA_KV_CACHE_TYPE: OLLAMA_LLM_LIBRARY: OLLAMA_LOAD_TIMEOUT:5m0s OLLAMA_MAX_LOADED_MODELS:0 OLLAMA_MAX_QUEUE:512 OLLAMA_MODELS:/usr/share/ollama/.ollama/models OLLAMA_MULTIUSER_CACHE:false OLLAMA_NEW_ENGINE:false OLLAMA_NOHISTORY:false OLLAMA_NOPRUNE:false OLLAMA_NUM_PARALLEL:1 OLLAMA_ORIGINS:[http://localhost https://localhost http://localhost:* https://localhost:* http://127.0.0.1 https://127.0.0.1 http://127.0.0.1:* https://127.0.0.1:* http://0.0.0.0 https://0.0.0.0 http://0.0.0.0:* https://0.0.0.0:* app://* file://* tauri://* vscode-webview://* vscode-file://*] OLLAMA_SCHED_SPREAD:false ROCR_VISIBLE_DEVICES: http_proxy: https_proxy: no_proxy:]"
Sep 19 10:07:00 raspberrypi ollama[840]: time=2025-09-19T10:07:00.936-04:00 level=INFO source=images.go:477 msg="total blobs: 5"
Sep 19 10:07:00 raspberrypi ollama[840]: time=2025-09-19T10:07:00.937-04:00 level=INFO source=images.go:484 msg="total unused blobs removed: 0"
Sep 19 10:07:00 raspberrypi ollama[840]: time=2025-09-19T10:07:00.938-04:00 level=INFO source=routes.go:1385 msg="Listening on 127.0.0.1:11434 (version 0.11.11)"
Sep 19 10:07:00 raspberrypi ollama[840]: time=2025-09-19T10:07:00.945-04:00 level=INFO source=gpu.go:217 msg="looking for compatible GPUs"
Sep 19 10:07:00 raspberrypi ollama[840]: time=2025-09-19T10:07:00.993-04:00 level=INFO source=gpu.go:388 msg="no compatible GPUs were discovered"
Sep 19 10:07:00 raspberrypi ollama[840]: time=2025-09-19T10:07:00.993-04:00 level=INFO source=types.go:131 msg="inference compute" id=0 library=cpu variant="" compute="" driver=0.0 name="" total="7.6 GiB" available="7.4 GiB"
Sep 19 10:07:00 raspberrypi ollama[840]: time=2025-09-19T10:07:00.993-04:00 level=INFO source=routes.go:1426 msg="entering low vram mode" "total vram"="7.6 GiB" threshold="20.0 GiB"
