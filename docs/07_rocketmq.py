"""
RocketMQ 快速入门示例
这是一个完整的示例，包含生产者和消费者的所有代码

功能说明：
1. 发送消息到MQ
2. 从MQ消费消息
3. 确认消息消费

使用方式：
- 运行整个脚本会依次执行：发送消息 -> 消费消息
- 也可以单独调用 produce_messages() 或 consume_messages() 函数

Author: Zichu
Date: 2025/12/02
"""

import time
import sys
from mq_http_sdk.mq_exception import MQExceptionBase
from mq_http_sdk.mq_producer import TopicMessage
from mq_http_sdk.mq_consumer import *
from mq_http_sdk.mq_client import MQClient

# ==================== 配置信息（写死，实际使用时需要另外创建topic和group） ====================
MQ_CONFIG = {
    # HTTP协议客户端接入点
    'server': 'http://YOUR_INSTANCE_ID.mqrest.cn-shanghai.aliyuncs.com',  # 请替换为你的实例接入点
    # AccessKey ID
    'access_key': 'YOUR_ALIYUN_ACCESS_KEY_ID',  # 请替换为你的阿里云 AccessKey ID
    # AccessKey Secret
    'secret_key': 'YOUR_ALIYUN_ACCESS_KEY_SECRET',  # 请替换为你的阿里云 AccessKey Secret
    # Topic名称
    'topic': 'LLMO_CRAWL_TASKS',
    # 消费者组ID
    'group_id': 'GID_LLMO_CRAWLER',
    # RocketMQ实例ID
    'instance_id': 'MQ_INST_1146510734876082_BYx1bcvG'
}

# ==================== 初始化MQ客户端 ====================
mq_client = MQClient(
    MQ_CONFIG['server'],
    MQ_CONFIG['access_key'],
    MQ_CONFIG['secret_key']
)

print("=" * 60)
print("RocketMQ 快速入门示例")
print("=" * 60)


# ==================== 生产者：发送消息 ====================
def produce_messages(message_count=5):
    """
    发送消息到MQ
    
    Args:
        message_count: 要发送的消息数量
    """
    print(f"\n[发送] 开始发送消息...")
    print(f"Topic: {MQ_CONFIG['topic']}")
    print(f"Instance ID: {MQ_CONFIG['instance_id']}")
    print(f"消息数量: {message_count}\n")
    
    # 获取生产者
    producer = mq_client.get_producer(
        MQ_CONFIG['instance_id'],
        MQ_CONFIG['topic']
    )
    
    success_count = 0
    fail_count = 0
    
    try:
        for i in range(message_count):
            try:
                # 创建消息
                msg = TopicMessage(
                    # 消息内容
                    f"这是测试消息 #{i+1}，发送时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
                    # 消息标签
                    "test"
                )
                
                # 设置消息的自定义属性
                msg.put_property("index", i)
                msg.put_property("timestamp", int(time.time()))
                
                # 设置消息的Key
                msg.set_message_key(f"TestMessageKey_{i}")
                
                # 发送消息
                re_msg = producer.publish_message(msg)
                
                print(f"[成功] 消息 #{i+1} 发送成功")
                print(f"   MessageID: {re_msg.message_id}")
                print(f"   BodyMD5: {re_msg.message_body_md5}\n")
                success_count += 1
                
            except MQExceptionBase as e:
                print(f"[失败] 消息 #{i+1} 发送失败: {e}\n")
                fail_count += 1
                
    except MQExceptionBase as e:
        if e.type == "TopicNotExist":
            print(f"[错误] Topic 不存在，请先创建 Topic: {MQ_CONFIG['topic']}")
            sys.exit(1)
        print(f"[错误] 发送消息时发生异常: {e}")
        
    print(f"[统计] 发送统计: 成功 {success_count} 条，失败 {fail_count} 条")
    return success_count


# ==================== 消费者：接收消息 ====================
def consume_messages(max_messages=10, wait_seconds=3, batch_size=3):
    """
    从MQ消费消息
    
    Args:
        max_messages: 最多消费的消息数量（防止无限循环）
        wait_seconds: 长轮询等待时间（秒）
        batch_size: 每次批量消费的消息数量（最大16）
    """
    print(f"\n[接收] 开始消费消息...")
    print(f"Topic: {MQ_CONFIG['topic']}")
    print(f"Group ID: {MQ_CONFIG['group_id']}")
    print(f"Instance ID: {MQ_CONFIG['instance_id']}")
    print(f"最多消费: {max_messages} 条")
    print(f"批量大小: {batch_size}\n")
    
    # 获取消费者
    consumer = mq_client.get_consumer(
        MQ_CONFIG['instance_id'],
        MQ_CONFIG['topic'],
        MQ_CONFIG['group_id']
    )
    
    consumed_count = 0
    no_message_count = 0
    max_no_message_retries = 3  # 连续3次无消息后停止
    
    try:
        while consumed_count < max_messages:
            try:
                # 长轮询消费消息
                recv_msgs = consumer.consume_message(batch_size, wait_seconds)
                
                if not recv_msgs:
                    no_message_count += 1
                    if no_message_count >= max_no_message_retries:
                        print(f"[提示] 连续 {max_no_message_retries} 次无新消息，停止消费\n")
                        break
                    continue
                
                # 重置无消息计数
                no_message_count = 0
                
                # 处理接收到的消息
                for msg in recv_msgs:
                    consumed_count += 1
                    print(f"[收到] 收到消息 #{consumed_count}")
                    print(f"   MessageID: {msg.message_id}")
                    print(f"   MessageTag: {msg.message_tag}")
                    print(f"   Body: {msg.message_body}")
                    print(f"   PublishTime: {msg.publish_time}")
                    print(f"   ConsumedTimes: {msg.consumed_times}")
                    print(f"   Properties: {msg.properties}")
                    print(f"   NextConsumeTime: {msg.next_consume_time}")
                    print()
                    
                # 确认消息消费成功
                try:
                    receipt_handle_list = [msg.receipt_handle for msg in recv_msgs]
                    consumer.ack_message(receipt_handle_list)
                    print(f"[确认] 成功确认 {len(receipt_handle_list)} 条消息\n")
                except MQExceptionBase as e:
                    print(f"[失败] 确认消息失败: {e}")
                    # 某些消息的句柄可能超时
                    if e.sub_errors:
                        for sub_error in e.sub_errors:
                            print(f"   ErrorHandle: {sub_error['ReceiptHandle']}")
                            print(f"   ErrorCode: {sub_error['ErrorCode']}")
                            print(f"   ErrorMsg: {sub_error['ErrorMessage']}")
                    print()
                    
            except MQExceptionBase as e:
                # Topic中没有消息可消费
                if e.type == "MessageNotExist":
                    no_message_count += 1
                    print(f"[提示] 暂无新消息 (RequestId: {e.req_id})")
                    if no_message_count >= max_no_message_retries:
                        print(f"[提示] 连续 {max_no_message_retries} 次无新消息，停止消费\n")
                        break
                    time.sleep(1)
                    continue
                    
                print(f"[失败] 消费消息失败: {e}\n")
                time.sleep(2)
                continue
                
    except KeyboardInterrupt:
        print(f"\n[中断] 用户中断消费")
        
    print(f"[统计] 消费统计: 共消费 {consumed_count} 条消息")
    return consumed_count


# ==================== 清空Topic消息（可选功能） ====================
def clear_topic_messages(topic_name=None, batch_size=16):
    """
    清空指定Topic中的所有消息
    
    Args:
        topic_name: Topic名称，不指定则使用配置中的默认Topic
        batch_size: 批量消费大小（最大16）
    """
    if topic_name is None:
        topic_name = MQ_CONFIG['topic']
        
    print(f"\n[清空] 开始清空 Topic: {topic_name}")
    
    consumer = mq_client.get_consumer(
        MQ_CONFIG['instance_id'],
        topic_name,
        MQ_CONFIG['group_id']
    )
    
    wait_seconds = 3
    message_count = 0
    
    try:
        while True:
            try:
                # 获取消息
                recv_msgs = consumer.consume_message(batch_size, wait_seconds)
                if not recv_msgs:
                    break
                    
                # 确认消息消费
                for msg in recv_msgs:
                    receipt_handle = msg.receipt_handle
                    consumer.ack_message([receipt_handle])
                    message_count += 1
                    
            except MQExceptionBase as e:
                if e.type == "MessageNotExist":
                    break
                print(f"[错误] 清空消息时出错: {e}")
                raise e
                
        print(f"[完成] 成功清空 {message_count} 条消息\n")
        return message_count
        
    except MQExceptionBase as e:
        print(f"[失败] 清空消息失败: {e}\n")
        raise e


# ==================== 主程序 ====================
def main():
    """
    主函数：演示完整的发送和接收流程
    """
    print("\n[演示] 开始演示 RocketMQ 完整流程\n")
    
    # 步骤1：发送消息
    print("=" * 60)
    print("步骤 1: 发送消息")
    print("=" * 60)
    sent_count = produce_messages(message_count=5)
    
    # 等待一下，确保消息已经在MQ中
    print("\n[等待] 等待 2 秒...")
    time.sleep(2)
    
    # 步骤2：消费消息
    print("\n" + "=" * 60)
    print("步骤 2: 消费消息")
    print("=" * 60)
    consumed_count = consume_messages(max_messages=10)
    
    # 总结
    print("\n" + "=" * 60)
    print("演示完成！")
    print(f"发送: {sent_count} 条")
    print(f"消费: {consumed_count} 条")
    print("=" * 60)


if __name__ == '__main__':
    # 运行主程序
    main()
    
    # 如果需要单独测试某个功能，可以注释掉上面的 main()，使用下面的代码：
    
    # 只发送消息
    # produce_messages(message_count=5)
    
    # 只消费消息
    # consume_messages(max_messages=10)
    
    # 清空Topic消息
    # clear_topic_messages()

