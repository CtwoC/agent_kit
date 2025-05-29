=== Non-Streaming Response ===
{
  "id": "chatcmpl-BcO1gPfCFAf86O5CyQ9CTeEyoc8KG",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "logprobs": null,
      "message": {
        "content": "Why don't skeletons fight each other? They don't have the guts.",
        "refusal": null,
        "role": "assistant",
        "annotations": [],
        "audio": null,
        "function_call": null,
        "tool_calls": null
      }
    }
  ],
  "created": 1748488520,
  "model": "gpt-4o-2024-08-06",
  "object": "chat.completion",
  "service_tier": "default",
  "system_fingerprint": "fp_a288987b44",
  "usage": {
    "completion_tokens": 14,
    "prompt_tokens": 23,
    "total_tokens": 37,
    "completion_tokens_details": {
      "accepted_prediction_tokens": 0,
      "audio_tokens": 0,
      "reasoning_tokens": 0,
      "rejected_prediction_tokens": 0
    },
    "prompt_tokens_details": {
      "audio_tokens": 0,
      "cached_tokens": 0
    }
  }
}

=== Tool Call Response ===
{
  "id": "chatcmpl-BcQ8ko2nz9B7CRvV0uVbcowidHpQU",
  "choices": [
    {
      "finish_reason": "tool_calls",
      "index": 0,
      "logprobs": null,
      "message": {
        "content": null,
        "refusal": null,
        "role": "assistant",
        "annotations": [],
        "audio": null,
        "function_call": null,
        "tool_calls": [
          {
            "id": "call_qOfTGgDrItLORNfC6VwUbyLL",
            "function": {
              "arguments": "{\"location\":\"Shanghai\"}",
              "name": "get_weather"
            },
            "type": "function"
          }
        ]
      }
    }
  ],
  "created": 1748496646,
  "model": "gpt-4o-2024-08-06",
  "object": "chat.completion",
  "service_tier": "default",
  "system_fingerprint": "fp_76544d79cb",
  "usage": {
    "completion_tokens": 14,
    "prompt_tokens": 91,
    "total_tokens": 105,
    "completion_tokens_details": {
      "accepted_prediction_tokens": 0,
      "audio_tokens": 0,
      "reasoning_tokens": 0,
      "rejected_prediction_tokens": 0
    },
    "prompt_tokens_details": {
      "audio_tokens": 0,
      "cached_tokens": 0
    }
  }
}

=== Streaming Response ===
[
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "",
          "function_call": null,
          "refusal": null,
          "role": "assistant",
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "Sure",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": ",",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": " here",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": " we",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": " go",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": ":\n\n",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "1",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "...\n\n",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "2",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "...\n\n",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "3",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "...\n\n",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "4",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "...\n\n",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": "5",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": ".",
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": null,
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  },
  {
    "id": "chatcmpl-BcO1hnPjEvZV3bFT9Qy3ioq7rq5Xj",
    "choices": [
      {
        "delta": {
          "content": null,
          "function_call": null,
          "refusal": null,
          "role": null,
          "tool_calls": null
        },
        "finish_reason": "stop",
        "index": 0,
        "logprobs": null
      }
    ],
    "created": 1748488521,
    "model": "gpt-4o-2024-08-06",
    "object": "chat.completion.chunk",
    "service_tier": "default",
    "system_fingerprint": "fp_a288987b44",
    "usage": null
  }
]



=== Streaming Tool Call Response ===
[
  {
    "response": {
      "id": "resp_6838085ccc98819890607476e8bea879001c774c11fd6e0c",
      "created_at": 1748502620.0,
      "error": null,
      "incomplete_details": null,
      "instructions": null,
      "metadata": {},
      "model": "gpt-4o-2024-08-06",
      "object": "response",
      "output": [],
      "parallel_tool_calls": true,
      "temperature": 0.7,
      "tool_choice": "auto",
      "tools": [
        {
          "name": "get_weather",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "City and country e.g. Bogot\u00e1, Colombia"
              }
            },
            "required": [
              "location"
            ],
            "additionalProperties": false
          },
          "strict": true,
          "type": "function",
          "description": "Get current temperature for a given location."
        }
      ],
      "top_p": 1.0,
      "max_output_tokens": null,
      "previous_response_id": null,
      "reasoning": {
        "effort": null,
        "generate_summary": null,
        "summary": null
      },
      "status": "in_progress",
      "text": {
        "format": {
          "type": "text"
        }
      },
      "truncation": "disabled",
      "usage": null,
      "user": null,
      "background": false,
      "service_tier": "auto",
      "store": true
    },
    "type": "response.created",
    "sequence_number": 0
  },
  {
    "response": {
      "id": "resp_6838085ccc98819890607476e8bea879001c774c11fd6e0c",
      "created_at": 1748502620.0,
      "error": null,
      "incomplete_details": null,
      "instructions": null,
      "metadata": {},
      "model": "gpt-4o-2024-08-06",
      "object": "response",
      "output": [],
      "parallel_tool_calls": true,
      "temperature": 0.7,
      "tool_choice": "auto",
      "tools": [
        {
          "name": "get_weather",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "City and country e.g. Bogot\u00e1, Colombia"
              }
            },
            "required": [
              "location"
            ],
            "additionalProperties": false
          },
          "strict": true,
          "type": "function",
          "description": "Get current temperature for a given location."
        }
      ],
      "top_p": 1.0,
      "max_output_tokens": null,
      "previous_response_id": null,
      "reasoning": {
        "effort": null,
        "generate_summary": null,
        "summary": null
      },
      "status": "in_progress",
      "text": {
        "format": {
          "type": "text"
        }
      },
      "truncation": "disabled",
      "usage": null,
      "user": null,
      "background": false,
      "service_tier": "auto",
      "store": true
    },
    "type": "response.in_progress",
    "sequence_number": 1
  },
  {
    "item": {
      "arguments": "",
      "call_id": "call_0wvaBfn8hir385b2vIJQpMMO",
      "name": "get_weather",
      "type": "function_call",
      "id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
      "status": "in_progress"
    },
    "output_index": 0,
    "type": "response.output_item.added",
    "sequence_number": 2
  },
  {
    "delta": "{\"",
    "item_id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
    "output_index": 0,
    "type": "response.function_call_arguments.delta",
    "sequence_number": 3
  },
  {
    "delta": "location",
    "item_id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
    "output_index": 0,
    "type": "response.function_call_arguments.delta",
    "sequence_number": 4
  },
  {
    "delta": "\":\"",
    "item_id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
    "output_index": 0,
    "type": "response.function_call_arguments.delta",
    "sequence_number": 5
  },
  {
    "delta": "Shanghai",
    "item_id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
    "output_index": 0,
    "type": "response.function_call_arguments.delta",
    "sequence_number": 6
  },
  {
    "delta": ",",
    "item_id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
    "output_index": 0,
    "type": "response.function_call_arguments.delta",
    "sequence_number": 7
  },
  {
    "delta": " China",
    "item_id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
    "output_index": 0,
    "type": "response.function_call_arguments.delta",
    "sequence_number": 8
  },
  {
    "delta": "\"}",
    "item_id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
    "output_index": 0,
    "type": "response.function_call_arguments.delta",
    "sequence_number": 9
  },
  {
    "arguments": "{\"location\":\"Shanghai, China\"}",
    "item_id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
    "output_index": 0,
    "type": "response.function_call_arguments.done",
    "sequence_number": 10
  },
  {
    "item": {
      "arguments": "{\"location\":\"Shanghai, China\"}",
      "call_id": "call_0wvaBfn8hir385b2vIJQpMMO",
      "name": "get_weather",
      "type": "function_call",
      "id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
      "status": "completed"
    },
    "output_index": 0,
    "type": "response.output_item.done",
    "sequence_number": 11
  },
  {
    "response": {
      "id": "resp_6838085ccc98819890607476e8bea879001c774c11fd6e0c",
      "created_at": 1748502620.0,
      "error": null,
      "incomplete_details": null,
      "instructions": null,
      "metadata": {},
      "model": "gpt-4o-2024-08-06",
      "object": "response",
      "output": [
        {
          "arguments": "{\"location\":\"Shanghai, China\"}",
          "call_id": "call_0wvaBfn8hir385b2vIJQpMMO",
          "name": "get_weather",
          "type": "function_call",
          "id": "fc_6838085d82248198bf5fe37afd4bdaec001c774c11fd6e0c",
          "status": "completed"
        }
      ],
      "parallel_tool_calls": true,
      "temperature": 0.7,
      "tool_choice": "auto",
      "tools": [
        {
          "name": "get_weather",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "City and country e.g. Bogot\u00e1, Colombia"
              }
            },
            "required": [
              "location"
            ],
            "additionalProperties": false
          },
          "strict": true,
          "type": "function",
          "description": "Get current temperature for a given location."
        }
      ],
      "top_p": 1.0,
      "max_output_tokens": null,
      "previous_response_id": null,
      "reasoning": {
        "effort": null,
        "generate_summary": null,
        "summary": null
      },
      "status": "completed",
      "text": {
        "format": {
          "type": "text"
        }
      },
      "truncation": "disabled",
      "usage": {
        "input_tokens": 67,
        "input_tokens_details": {
          "cached_tokens": 0
        },
        "output_tokens": 17,
        "output_tokens_details": {
          "reasoning_tokens": 0
        },
        "total_tokens": 84
      },
      "user": null,
      "background": false,
      "service_tier": "default",
      "store": true
    },
    "type": "response.completed",
    "sequence_number": 12
  }
]





finish_reason	说明
stop	正常结束，遇到 stop sequence，或自然结束。
length	达到 max_tokens 限制。
tool_calls	模型决定调用工具（tool calls）。
function_call	模型决定调用函数（老版本 function calling 模式）。
content_filter	模型的输出被内容过滤系统拦截，内容未返回。
null	流式响应时，当前 chunk 尚未完成，暂为 null。