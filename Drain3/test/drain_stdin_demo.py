# SPDX-License-Identifier: MIT

import json
import logging
import sys
from os.path import dirname

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

# persistence_type = "NONE"
# persistence_type = "REDIS"
# persistence_type = "KAFKA"
persistence_type = "FILE"

logger = logging.getLogger(__name__)  #生成logger实例
#设置日志级别：INFO类型 用来记录关键代价点的信息。format参数用来设置日志的格式 %(message)s记入日志的消息记录
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')


if persistence_type == "KAFKA":
    from drain3.kafka_persistence import KafkaPersistence

    persistence = KafkaPersistence("drain3_state", bootstrap_servers="localhost:9092")

elif persistence_type == "FILE":
    from drain3.file_persistence import FilePersistence

    persistence = FilePersistence("drain3_state.bin")

elif persistence_type == "REDIS":
    from drain3.redis_persistence import RedisPersistence

    persistence = RedisPersistence(redis_host='',
                                   redis_port=25061,
                                   redis_db=0,
                                   redis_pass='',
                                   is_ssl=True,
                                   redis_key="drain3_state_key")
else:
    persistence = None

config = TemplateMinerConfig()    #用于加载配置文件的类
config.load(dirname(__file__) + "/drain3.ini")    #dirname(__file__)返回 本文件所在的绝对路径
config.profiling_enabled = False

template_miner = TemplateMiner(persistence, config)
print(f"Drain3 started with '{persistence_type}' persistence")
print(f"{len(config.masking_instructions)} masking instructions are in use")
print(f"Starting training mode. Reading from std-in ('q' to finish)")

while True:

    log_line = input("> ")
    if log_line == 'q':
        break
    result = template_miner.add_log_message(log_line)
    result_json = json.dumps(result)                #把python数据类型转换为json
    print(result_json)
    template = result["template_mined"]
    params = template_miner.extract_parameters(template, log_line)
    print("Parameters: " + str(params))

print("Training done. Mined clusters:")
for cluster in template_miner.drain.clusters:
    print(cluster)

print(f"Starting inference mode, matching to pre-trained clusters. Input log lines or 'q' to finish")
test_file = "log/log semantics anomaly detection/error.csv"
while True:

    log_line = input("> ")
    if log_line == 'q':
        break
    cluster = template_miner.match(log_line)
    if cluster is None:
        print(f"No match found")
    else:
        template = cluster.get_template()
        print(f"Matched template #{cluster.cluster_id}: {template}")
        print(f"Parameters: {template_miner.get_parameter_list(template, log_line)}")
