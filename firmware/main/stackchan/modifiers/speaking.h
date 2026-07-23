/* 
 * SPDX-FileCopyrightText: 2026 M5Stack Technology CO LTD
 *
 * SPDX-License-Identifier: MIT
 */
#pragma once
#include "../modifiable.h"
#include "../utils/random.h"
#include <smooth_ui_toolkit.hpp>
#include <hal/hal.h>
#include <algorithm>
#include <cstdint>

namespace stackchan {

class SpeakingModifier : public Modifier {
public:
    enum class Emotion {
        Neutral,
        Happy,
        Sad,
        Curious,
        Excited,
        Thoughtful,
        Surprised,
        Sleepy
    };

    /**
     * @param destroyAfterMs 持续说话时间（0 为永久，直到手动移除）
     * @param mouthIntervalMs 嘴巴开合频率（默认 180ms）
     * @param enableMotion 是否在说话时伴随头部微动
     * @param emotion 当前说话情绪（影响动作幅度、嘴巴速度、灯光）
     */
    SpeakingModifier(uint32_t destroyAfterMs = 0,
                     uint32_t mouthIntervalMs = 180,
                     bool enableMotion = true,
                     Emotion emotion = Emotion::Neutral)
        : _mouth_interval_ms(mouthIntervalMs),
          _enable_motion(enableMotion),
          _emotion(emotion)
    {
        uint32_t now = GetHAL().millis();

        // 销毁计时
        if (destroyAfterMs > 0) {
            _destroy_at   = now + destroyAfterMs;
            _has_lifetime = true;
        }

        // 嘴巴计时（情绪会影响基础间隔）
        _next_mouth_tick = now + _mouth_interval_ms;

        // 动作计时
        if (_enable_motion) {
            _next_motion_tick = now + Random::getInstance().getInt(800, 1800);
        }

        _need_get_prev_angles = true;

        // 根据情绪调整初始参数
        _apply_emotion_scales();
    }

    void setEmotion(Emotion emotion) {
        _emotion = emotion;
        _apply_emotion_scales();
    }

    void _update(Modifiable& stackchan) override
    {
        if (!stackchan.hasAvatar()) {
            return;
        }

        uint32_t now = GetHAL().millis();

        // 检查销毁逻辑
        if (_has_lifetime && now >= _destroy_at) {
            stackchan.avatar().mouth().setWeight(0);  // 闭嘴
            requestDestroy();
            return;
        }

        // 嘴巴开合动画
        if (now >= _next_mouth_tick) {
            _next_mouth_tick = now + static_cast<uint32_t>(_mouth_interval_ms * _mouth_speed_scale);
            animate_mouth(stackchan.avatar());
        }

        // 身体微动动作（情绪化）
        if (_enable_motion && now >= _next_motion_tick) {
            uint32_t base_delay = static_cast<uint32_t>(1800 * (2.0f - _motion_amplitude_scale));
            _next_motion_tick = now + Random::getInstance().getInt(base_delay - 300, base_delay + 500);
            perform_subtle_speaking_motion(stackchan);
        }

        // 情绪化灯光反馈（简单脉冲）
        if (_light_intensity > 0.4f && (now / 300) % 2 == 0) {
            // 轻微 neon 脉冲（可根据实际 neon API 调整）
            // stackchan.leftNeonLight().setBrightness(...);
        }
    }

private:
    void animate_mouth(avatar::Avatar& avatar)
    {
        _is_mouth_open = !_is_mouth_open;
        auto& random   = Random::getInstance();

        int weight = _is_mouth_open ? random.getInt(_open_min_weight, _open_max_weight)
                                    : random.getInt(_close_min_weight, _close_max_weight);

        avatar.mouth().setWeight(weight);

        // 轻微旋转增加表现力（情绪化）
        if (_emotion == Emotion::Happy || _emotion == Emotion::Excited) {
            int rot = random.getInt(-15, 15);
            avatar.mouth().setRotation(rot < 0 ? 3600 + rot : rot);
        }
    }

    void perform_subtle_speaking_motion(Modifiable& stackchan)
    {
        auto& motion = stackchan.motion();
        if (motion.isMoving()) {
            return;
        }

        uitk::Vector2i current_actual_angles = motion.getCurrentAngles();

        if (_need_get_prev_angles) {
            _prev_angles          = current_actual_angles;
            _home_angles          = current_actual_angles;
            _need_get_prev_angles = false;
        } else {
            const int32_t threshold = 300;
            int32_t diff_x          = std::abs(current_actual_angles.x - _prev_angles.x);
            int32_t diff_y          = std::abs(current_actual_angles.y - _prev_angles.y);

            if (diff_x > threshold || diff_y > threshold) {
                _prev_angles = current_actual_angles;
            }
        }

        int32_t target_yaw   = _prev_angles.x;
        int32_t target_pitch = _prev_angles.y;

        int action = Random::getInstance().getInt(0, 10);
        int speed  = static_cast<int>(Random::getInstance().getInt(80, 220) * _motion_amplitude_scale);

        int amp = static_cast<int>(40 * _motion_amplitude_scale);

        if (action < 5) {
            // 点头（情绪化幅度）
            target_pitch += Random::getInstance().getInt(-amp/2, amp);
        } else {
            // 摆头
            target_yaw   += Random::getInstance().getInt(-amp, amp);
            target_pitch += Random::getInstance().getInt(-amp/2, amp/2);
        }

        const auto yaw_limits = motion.yawServo().getAngleLimit();
        const auto pitch_limits = motion.pitchServo().getAngleLimit();
        const int safe_pitch_min = std::max(pitch_limits.x, _home_angles.y);
        const int safe_pitch_max = pitch_limits.y;
        target_yaw = uitk::clamp(target_yaw, yaw_limits.x, yaw_limits.y);
        target_pitch = uitk::clamp(target_pitch, safe_pitch_min, safe_pitch_max);

        motion.moveWithSpeed(target_yaw, target_pitch, speed);
    }

    void _apply_emotion_scales() {
        switch (_emotion) {
            case Emotion::Happy:
            case Emotion::Excited:
                _motion_amplitude_scale = 1.65f;
                _mouth_speed_scale      = 0.72f;
                _light_intensity        = 0.85f;
                _mouth_interval_ms      = 135;
                break;
            case Emotion::Sad:
            case Emotion::Sleepy:
                _motion_amplitude_scale = 0.45f;
                _mouth_speed_scale      = 1.45f;
                _light_intensity        = 0.18f;
                _mouth_interval_ms      = 290;
                break;
            case Emotion::Curious:
            case Emotion::Thoughtful:
                _motion_amplitude_scale = 0.85f;
                _mouth_speed_scale      = 1.05f;
                _light_intensity        = 0.55f;
                break;
            case Emotion::Surprised:
                _motion_amplitude_scale = 2.1f;
                _mouth_speed_scale      = 0.58f;
                _light_intensity        = 0.95f;
                _mouth_interval_ms      = 115;
                break;
            default: // Neutral
                _motion_amplitude_scale = 1.0f;
                _mouth_speed_scale      = 1.0f;
                _light_intensity        = 0.38f;
                break;
        }
    }

    // 配置常量（会被情绪缩放）
    int _open_min_weight  = 32;
    int _open_max_weight  = 88;
    int _close_min_weight = 0;
    int _close_max_weight = 22;

    // 情绪缩放
    float _motion_amplitude_scale = 1.0f;
    float _mouth_speed_scale      = 1.0f;
    float _light_intensity        = 0.35f;

    // 计时状态
    uint32_t _destroy_at       = 0;
    uint32_t _next_mouth_tick  = 0;
    uint32_t _next_motion_tick = 0;
    uint32_t _mouth_interval_ms;

    bool _has_lifetime         = false;
    bool _enable_motion        = false;
    bool _is_mouth_open        = false;
    bool _need_get_prev_angles = true;

    Emotion _emotion = Emotion::Neutral;
    uitk::Vector2i _prev_angles;
    uitk::Vector2i _home_angles;
};

}  // namespace stackchan
