=== Non-Streaming Response ===
{
  "id": "msg_014Uw1JoDTgUPWXt7GKRFRK3",
  "content": [
    {
      "text": "Why don't scientists trust atoms?\n\nBecause they make up everything!",
      "type": "text"
    }
  ],
  "model": "claude-3-7-sonnet-20250219",
  "role": "assistant",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "type": "message",
  "usage": {
    "input_tokens": 13,
    "output_tokens": 17,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "service_tier": "standard"
  }
}

=== Tool Call Response ===
{
  "id": "msg_01Fi1EqjDkLZWb48cXrdMGpM",
  "content": [
    {
      "text": "I'll check the current weather in Shanghai for you.",
      "type": "text"
    },
    {
      "id": "toolu_01WppHnD3srgami8yc44A9q9",
      "input": {
        "location": "Shanghai"
      },
      "name": "get_weather",
      "type": "tool_use"
    }
  ],
  "model": "claude-3-7-sonnet-20250219",
  "role": "assistant",
  "stop_reason": "tool_use",
  "stop_sequence": null,
  "type": "message",
  "usage": {
    "input_tokens": 402,
    "output_tokens": 65,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "service_tier": "standard"
  }
}

=== Streaming Response ===
[
  {
    "message": {
      "id": "msg_01SevfHzMZBgWbNYMYqbh4mk",
      "content": [],
      "model": "claude-3-7-sonnet-20250219",
      "role": "assistant",
      "stop_reason": null,
      "stop_sequence": null,
      "type": "message",
      "usage": {
        "input_tokens": 18,
        "output_tokens": 5,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "service_tier": "standard"
      }
    },
    "type": "message_start"
  },
  {
    "content_block": {
      "text": "",
      "type": "text"
    },
    "index": 0,
    "type": "content_block_start"
  },
  {
    "delta": {
      "text": "I'll count from ",
      "type": "text_delta"
    },
    "index": 0,
    "type": "content_block_delta"
  },
  {
    "delta": {
      "text": "1 to 5 slowly:\n\n1",
      "type": "text_delta"
    },
    "index": 0,
    "type": "content_block_delta"
  },
  {
    "delta": {
      "text": "\n.\n.\n2",
      "type": "text_delta"
    },
    "index": 0,
    "type": "content_block_delta"
  },
  {
    "delta": {
      "text": "\n.\n.\n3\n.\n.",
      "type": "text_delta"
    },
    "index": 0,
    "type": "content_block_delta"
  },
  {
    "delta": {
      "text": "\n4\n.",
      "type": "text_delta"
    },
    "index": 0,
    "type": "content_block_delta"
  },
  {
    "delta": {
      "text": "\n.\n5",
      "type": "text_delta"
    },
    "index": 0,
    "type": "content_block_delta"
  },
  {
    "index": 0,
    "type": "content_block_stop"
  },
  {
    "delta": {
      "stop_reason": "end_turn",
      "stop_sequence": null
    },
    "type": "message_delta",
    "usage": {
      "output_tokens": 42
    }
  },
  {
    "type": "message_stop"
  }
]



=== Streaming Tool Call Response ===
[
  {
    "message": {
      "id": "msg_01Vaw4c2mp6oGQtdjGmbacUz",
      "content": [],
      "model": "claude-3-7-sonnet-20250219",
      "role": "assistant",
      "stop_reason": null,
      "stop_sequence": null,
      "type": "message",
      "usage": {
        "input_tokens": 402,
        "output_tokens": 1,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "service_tier": "standard"
      }
    },
    "type": "message_start"
  },
  {
    "content_block": {
      "text": "",
      "type": "text"
    },
    "index": 0,
    "type": "content_block_start"
  },
  {
    "delta": {
      "text": "I",
      "type": "text_delta"
    },
    "index": 0,
    "type": "content_block_delta"
  },
  {
    "type": "text",
    "text": "I",
    "snapshot": "I"
  },
  {
    "delta": {
      "text": "'ll check the current weather in Shanghai for you.",
      "type": "text_delta"
    },
    "index": 0,
    "type": "content_block_delta"
  },
  {
    "type": "text",
    "text": "'ll check the current weather in Shanghai for you.",
    "snapshot": "I'll check the current weather in Shanghai for you."
  },
  {
    "index": 0,
    "type": "content_block_stop",
    "content_block": {
      "text": "I'll check the current weather in Shanghai for you.",
      "type": "text"
    }
  },
  {
    "content_block": {
      "id": "toolu_01KGQpAS75CWgVpsNNaT2akB",
      "input": {},
      "name": "get_weather",
      "type": "tool_use"
    },
    "index": 1,
    "type": "content_block_start"
  },
  {
    "delta": {
      "partial_json": "",
      "type": "input_json_delta"
    },
    "index": 1,
    "type": "content_block_delta"
  },
  {
    "type": "input_json",
    "partial_json": "",
    "snapshot": {}
  },
  {
    "delta": {
      "partial_json": "{\"",
      "type": "input_json_delta"
    },
    "index": 1,
    "type": "content_block_delta"
  },
  {
    "type": "input_json",
    "partial_json": "{\"",
    "snapshot": {}
  },
  {
    "delta": {
      "partial_json": "loca",
      "type": "input_json_delta"
    },
    "index": 1,
    "type": "content_block_delta"
  },
  {
    "type": "input_json",
    "partial_json": "loca",
    "snapshot": {}
  },
  {
    "delta": {
      "partial_json": "tion\": \"S",
      "type": "input_json_delta"
    },
    "index": 1,
    "type": "content_block_delta"
  },
  {
    "type": "input_json",
    "partial_json": "tion\": \"S",
    "snapshot": {}
  },
  {
    "delta": {
      "partial_json": "hanghai\"}",
      "type": "input_json_delta"
    },
    "index": 1,
    "type": "content_block_delta"
  },
  {
    "type": "input_json",
    "partial_json": "hanghai\"}",
    "snapshot": {
      "location": "Shanghai"
    }
  },
  {
    "index": 1,
    "type": "content_block_stop",
    "content_block": {
      "id": "toolu_01KGQpAS75CWgVpsNNaT2akB",
      "input": {
        "location": "Shanghai"
      },
      "name": "get_weather",
      "type": "tool_use"
    }
  },
  {
    "delta": {
      "stop_reason": "tool_use",
      "stop_sequence": null
    },
    "type": "message_delta",
    "usage": {
      "output_tokens": 65
    }
  },
  {
    "type": "message_stop",
    "message": {
      "id": "msg_01Vaw4c2mp6oGQtdjGmbacUz",
      "content": [
        {
          "text": "I'll check the current weather in Shanghai for you.",
          "type": "text"
        },
        {
          "id": "toolu_01KGQpAS75CWgVpsNNaT2akB",
          "input": {
            "location": "Shanghai"
          },
          "name": "get_weather",
          "type": "tool_use"
        }
      ],
      "model": "claude-3-7-sonnet-20250219",
      "role": "assistant",
      "stop_reason": "tool_use",
      "stop_sequence": null,
      "type": "message",
      "usage": {
        "input_tokens": 402,
        "output_tokens": 65,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "service_tier": "standard"
      }
    }
  }
]

stop_reason	说明
stop_sequence	模型输出命中了 stop_sequences 中的某个值。正常结束。
max_tokens	达到 max_tokens 限制，强制截断。
tool_use	Claude 选择调用一个工具（如函数）。在调用工具后会返回此 stop_reason。
end_turn	Claude 判断用户和模型的一轮对话结束（用于多轮交互系统）。
null	只有在流式响应中，中间某个 chunk 没有终止条件时会是 null。最终一个 chunk 一定会包含非 null 的 stop_reason。