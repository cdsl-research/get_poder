from kubernetes import client, config, stream

# Kubernetesクラスタへの接続
config.load_kube_config()

# Kubernetes APIの初期化
v1 = client.CoreV1Api()

# 全てのネームスペースのPodのリストを取得
pods = v1.list_pod_for_all_namespaces(watch=False)

storage_info = None

for pod in pods.items:
    if pod.metadata.namespace != "kube-system":
        try:
            # コンテナ内で df コマンドを実行し、ストレージ使用量を取得
            command = ['df', '-h']
            resp = stream.stream(v1.connect_get_namespaced_pod_exec, pod.metadata.name, 
                                 pod.metadata.namespace, command=command, 
                                 stderr=True, stdin=False, stdout=True, tty=False)
            
            # '/var'を含む行からストレージ情報を取得
            for line in resp.split('\n'):
                if '/var' in line:
                    parts = line.split()
                    if len(parts) >= 6 and not storage_info:
                        # 最初に見つかったストレージ情報を保存
                        storage_info = f"{parts[1]}  {parts[2]}  {parts[3]}  {parts[4]}"
                        nfs_size = parts[1]
                        break
        except Exception as e:
            print(f"Error executing command in pod {pod.metadata.name}: {e}")
        if storage_info:
            # 最初に見つかったストレージ情報があればループを終了
            break

# NFS-Storage情報を出力
if storage_info:
    print("NFS-Storage")
    print("Size  Used Avail Use%")
    print(storage_info)
else:
    print("NFS-Storage情報が見つかりませんでした。")