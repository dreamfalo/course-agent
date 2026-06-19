-- ============================================================
-- 智能课程助手 Agent - MySQL 8.0 建表脚本
-- 数据库: course_agent_db
-- 可直接在 Navicat / MySQL Workbench 中执行
-- ============================================================

CREATE DATABASE IF NOT EXISTS course_agent_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE course_agent_db;

-- 1. 用户表
CREATE TABLE IF NOT EXISTS system_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME(6) NULL,
    is_superuser TINYINT(1) NOT NULL DEFAULT 0,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_staff TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    date_joined DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    role VARCHAR(16) NOT NULL DEFAULT 'student',
    avatar VARCHAR(200) NOT NULL DEFAULT '',
    phone VARCHAR(20) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 课表表
CREATE TABLE IF NOT EXISTS user_schedule (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    course_id VARCHAR(64) NOT NULL UNIQUE,
    course_name VARCHAR(128) NOT NULL,
    teacher VARCHAR(64) NOT NULL DEFAULT '待定',
    weekday SMALLINT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location VARCHAR(128) NOT NULL DEFAULT '待定',
    week_range VARCHAR(32) NOT NULL DEFAULT '1-16',
    semester VARCHAR(32) NOT NULL DEFAULT '2025-2026-2',
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_user_semester (user_id, semester),
    INDEX idx_user_weekday (user_id, weekday)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. RAG 知识库文档表
CREATE TABLE IF NOT EXISTS user_knowledge_file (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    course_id VARCHAR(64) NOT NULL,
    doc_id VARCHAR(256) NOT NULL UNIQUE,
    file_name VARCHAR(256) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(16) NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    chunks_count INT NOT NULL DEFAULT 0,
    course_name VARCHAR(128) NOT NULL DEFAULT '',
    status VARCHAR(16) NOT NULL DEFAULT 'uploaded',
    uploaded_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_user_course (user_id, course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 学习任务表
CREATE TABLE IF NOT EXISTS user_task (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    plan_id VARCHAR(64) NOT NULL,
    task_id VARCHAR(64) NOT NULL UNIQUE,
    task_name VARCHAR(256) NOT NULL,
    subject VARCHAR(64) NOT NULL,
    date DATE NOT NULL,
    weekday SMALLINT NOT NULL DEFAULT 0,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 0,
    progress INT NOT NULL DEFAULT 0,
    dependencies JSON DEFAULT NULL,
    plan_config JSON DEFAULT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    generated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_user_plan (user_id, plan_id),
    INDEX idx_user_date (user_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 对话历史表
CREATE TABLE IF NOT EXISTS agent_chat_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    role VARCHAR(16) NOT NULL,
    content LONGTEXT NOT NULL,
    tool_calls JSON DEFAULT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_user_session (user_id, session_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(128) NOT NULL UNIQUE,
    config_value LONGTEXT NOT NULL,
    config_type VARCHAR(32) NOT NULL DEFAULT 'string',
    category VARCHAR(32) NOT NULL DEFAULT 'general',
    description VARCHAR(256) NOT NULL DEFAULT '',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初始化默认配置
INSERT INTO system_config (config_key, config_value, config_type, category, description) VALUES
('deepseek_api_key', '', 'secret', 'llm', 'DeepSeek API 密钥'),
('deepseek_api_base', 'https://api.deepseek.com/v1', 'string', 'llm', 'DeepSeek API 地址'),
('deepseek_model', 'deepseek-chat', 'string', 'llm', '默认对话模型'),
('deepseek_temperature', '0.7', 'string', 'llm', '默认温度参数'),
('deepseek_max_tokens', '4096', 'int', 'llm', '最大输出 Token 数'),
('chroma_persist_dir', './chroma_db', 'string', 'vector', 'Chroma 持久化目录'),
('chroma_chunk_size', '500', 'int', 'vector', '文档分块大小'),
('chroma_chunk_overlap', '50', 'int', 'vector', '分块重叠大小'),
('minio_endpoint', 'localhost:9000', 'string', 'storage', 'MinIO 服务地址'),
('minio_bucket', 'course-files', 'string', 'storage', 'MinIO 存储桶'),
('file_temp_ttl_hours', '24', 'int', 'storage', '临时文件有效期(小时)'),
('notification_enabled', 'true', 'bool', 'notification', '是否启用消息提醒'),
('default_role', 'student', 'string', 'general', '新用户默认角色')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP(6);
