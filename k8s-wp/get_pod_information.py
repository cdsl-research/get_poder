from kubernetes import client, config, stream
import time

# Kubernetesクラスタへの接続
config.load_kube_config()

# Kubernetes APIの初期化
v1 = client.CoreV1Api()

# PVCのキャパシティ情報を取得
pvc_capacity = {}
pvc_list = v1.list_persistent_volume_claim_for_all_namespaces()
for pvc in pvc_list.items:
    capacity = pvc.status.capacity.get('storage')
    if capacity:
        # 'Gi'を取り除いて数値に変換
        numeric_capacity = float(capacity.replace('Gi', ''))
    else:
        numeric_capacity = '不明'
    pvc_capacity[pvc.metadata.name] = numeric_capacity

# 全てのネームスペースのPodのリストを取得
pods = v1.list_pod_for_all_namespaces(watch=False)

for pod in pods.items:
    if pod.metadata.namespace != "kube-system":
        try:
            # コンテナ内で du コマンドを実行し、/var のストレージ使用量を取得
            command = ['du', '-sh', '/var']
            resp = stream.stream(v1.connect_get_namespaced_pod_exec, pod.metadata.name, 
                                 pod.metadata.namespace, command=command, 
                                 stderr=True, stdin=False, stdout=True, tty=False)
            
            print(f"Pod: {pod.metadata.name}")
            # 出力の解析とフォーマット
            lines = resp.split('\n')
            if lines:
                size_info = lines[0].split('\t')[0]  # 'du' コマンドの出力からサイズ情報を取得
                if 'M' in size_info:
                    # MBをGBに変換
                    size_in_gb = round(float(size_info.replace('M', '')) / 1024, 2)
                else:
                    # 'G'を取り除いて数値に変換
                    size_in_gb = float(size_info.replace('G', ''))
                print(f" Size: {size_in_gb}G")

            # 対応するPVCのキャパシティを表示
            for volume in pod.spec.volumes:
                if volume.persistent_volume_claim:
                    pvc_name = volume.persistent_volume_claim.claim_name
                    print(f" CAPACITY: {pvc_capacity.get(pvc_name, '不明')}Gi")
        except Exception as e:
            print(f"Error executing command in pod {pod.metadata.name}: {e}")