#%% 导入必要的库
from prompt_optimizer import PromptOptimizer
import mysql.connector
from typing import Optional

#%% 定义示例prompt和优化建议
def get_db_connection():
    # 数据库配置
    db_config = {
        "host": "rm-uf6460x8sj8242fn64o.mysql.rds.aliyuncs.com",
        "user": "yj_app",
        "password": "4iLe5fifhMqOo9Ne",
        "database": "kaogong"
    }
    return mysql.connector.connect(**db_config)

def get_role_id_by_sid(sid: str) -> Optional[int]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id FROM role_config WHERE sid = %s"
        cursor.execute(query, (sid,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result['id'] if result else None
        
    except Exception as e:
        print(f"获取role_id错误: {e}")
        return None

def get_version_by_role_env(role_id: int, prompt_type: str, env: str) -> Optional[str]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT version FROM role_prompt_env WHERE role_id = %s AND prompt_type = %s AND env = %s"
        cursor.execute(query, (role_id, prompt_type, env))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result['version'] if result else None
        
    except Exception as e:
        print(f"获取version错误: {e}")
        return None

def get_role_prompt(sid: str, prompt_type: str, env: str = 'dev') -> Optional[str]:
    try:
        # 获取role_id
        role_id = get_role_id_by_sid(sid)
        if role_id is None:
            print(f"未找到sid={sid}对应的role_id")
            return None
            
        # 获取version
        version = get_version_by_role_env(role_id, prompt_type, env)
        if version is None:
            print(f"未找到role_id={role_id}, env={env}对应的version")
            return None
        
        # 获取prompt内容
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT content 
        FROM role_prompt 
        WHERE role_id = %s 
          AND prompt_type = %s 
          AND version = %s 
          AND is_active = 1
        """
        
        cursor.execute(query, (role_id, prompt_type, version))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return result['content']
        return None
        
    except Exception as e:
        print(f"获取prompt错误: {e}")
        return None

# 从数据库获取prompt
sid = 'huatu_WX'  # 角色标识符
prompt_type = 'role_prompt'  # prompt类型
env = 'dev'  # 环境

original_prompt = get_role_prompt(sid, prompt_type, env)
print(f"original_prompt:\n{original_prompt}")
if original_prompt is None:
    original_prompt = """
    你是一个AI助手。
    帮助用户解决问题。
    回答要简洁。
    """
    print("未能从数据库获取prompt，使用默认prompt")


# 优化建议
optimization_suggestions = """
1. 需要更具体地定义AI助手的专业领域
2. 添加更多关于回答格式的具体要求
3. 增加对用户输入的处理规则
4. 添加一些示例来说明如何回答
"""

#%% 使用OpenAI优化器
try:
    print("=== 使用 OpenAI 优化 ===\n")
    # 默认API端点
    openai_optimizer = PromptOptimizer.create("openai")
    openai_result = openai_optimizer.optimize(
        original_prompt=original_prompt,
        optimization_suggestions=optimization_suggestions
    )
    print("默认API端点结果:")
    print(openai_result)
    
    # # 使用自定义API端点
    # print("\n=== 使用自定义OpenAI端点 ===\n")
    # custom_openai_optimizer = PromptOptimizer.create(
    #     "openai",
    #     base_url="http://43.130.31.174:8003/v1"  # 替换为你的自定义端点
    # )
    # custom_result = custom_openai_optimizer.optimize(
    #     original_prompt=original_prompt,
    #     optimization_suggestions=optimization_suggestions
    # )
    # print("自定义端点结果:")
    # print(custom_result)
except Exception as e:
    print(f"OpenAI优化出错: {str(e)}")

#%% 比较优化前后的差异
def show_prompt_diff(original: str, optimized: str, title: str = "Prompt对比"):
    import difflib
    from datetime import datetime
    
    # 将字符串分割成行
    original_lines = original.splitlines()
    optimized_lines = optimized.splitlines()
    
    # 创建差异比较器
    differ = difflib.HtmlDiff()
    
    # 生成HTML格式的差异报告
    diff_html = differ.make_file(
        original_lines,
        optimized_lines,
        "原始Prompt",
        "优化后Prompt",
        context=True
    )
    
    # 保存差异报告到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prompt_diff_{timestamp}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(diff_html)
    print(f"\n差异报告已保存到文件: {filename}")

# 显示OpenAI优化结果的差异
if 'openai_result' in locals():
    print("\n=== OpenAI优化结果对比 ===\n")
    show_prompt_diff(original_prompt, openai_result)

#%% 使用Claude优化器
try:
    print("\n=== 使用 Claude 优化 ===\n")
    # 默认API端点
    claude_optimizer = PromptOptimizer.create("claude")
    claude_result = claude_optimizer.optimize(
        original_prompt=original_prompt,
        optimization_suggestions=optimization_suggestions
    )
    print("默认API端点结果:")
    print(claude_result)
    
    # 显示Claude优化结果的差异
    print("\n=== Claude优化结果对比 ===\n")
    show_prompt_diff(original_prompt, claude_result)
    
    # 使用自定义API端点
    # print("\n=== 使用自定义Claude端点 ===\n")
    # custom_claude_optimizer = PromptOptimizer.create(
    #     "claude" # 替换为你的自定义端点
    # )
    # custom_result = custom_claude_optimizer.optimize(
    #     original_prompt=original_prompt,
    #     optimization_suggestions=optimization_suggestions
    # )
    # print("自定义端点结果:")
    # print(custom_result)
except Exception as e:
    print(f"Claude优化出错: {str(e)}")

# %%
# 如果优化成功，插入新的prompt记录
def insert_optimized_prompt(role_id: int, prompt_type: str, content: str, version: str) -> bool:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 插入新的prompt记录
        query = """
        INSERT INTO role_prompt 
        (role_id, prompt_type, content, version, is_active, create_time, update_time) 
        VALUES (%s, %s, %s, %s, 1, NOW(), NOW())
        """
        cursor.execute(query, (role_id, prompt_type, content, version))
        
        # 将同一role_id和prompt_type的其他记录设置为非激活
        update_query = """
        UPDATE role_prompt 
        SET is_active = 0 
        WHERE role_id = %s 
          AND prompt_type = %s 
          AND version != %s
        """
        cursor.execute(update_query, (role_id, prompt_type, version))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"插入优化后的prompt错误: {e}")
        return False

new_version = "1.1"  # 在原来version基础上增加
success = insert_optimized_prompt(
    role_id=role_id,
    prompt_type=prompt_type,
    content=openai_result,
    version=new_version
)

#%%
# 如果插入成功，更新环境中的version
def update_prompt_version(role_id: int, prompt_type: str, env: str, new_version: str) -> bool:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新version
        query = """
        UPDATE role_prompt_env 
        SET version = %s,
            update_time = NOW()
        WHERE role_id = %s 
          AND prompt_type = %s 
          AND env = %s
        """
        cursor.execute(query, (new_version, role_id, prompt_type, env))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"更新prompt version错误: {e}")
        return False

# 2. 如果插入成功，更新环境中的version
if success:
    success = update_prompt_version(
        role_id=role_id,
        prompt_type=prompt_type,
        env=env,
        new_version=new_version
    )

# %%
