/*
 * SPDX-FileCopyrightText: 2026 M5Stack Technology CO LTD
 *
 * SPDX-License-Identifier: MIT
 */
#pragma once
#include "../modifiable.h"
#include "../utils/random.h"
#include "speaking.h"
#include <smooth_ui_toolkit.hpp>
#include <hal/hal.h>
#include <algorithm>
#include <cstdint>

namespace stackchan {

/**
 * @brief 情绪化表情驱动器
 * 
 * 由本地后端（PelicanAI）通过 set_emotion() 驱动。
 * 负责空闲时的情绪化行为：眼动、头部姿态、眨眼频率、嘴巴休息姿势、灯光等。
 */
class EmotionalExpressionModifier : public Modifier {
public:
    using Emotion = SpeakingModifier::Emotion;

    EmotionalExpressionModifier(Emotion initial = Emotion::Neutral, float intensity = 0.7f)
        : _emotion(initial), _intensity(intensity)
    {
        _next_tick = GetHAL().millis() + 800;
    }

    void setEmotion(Emotion emotion, float intensity = 0.7f) {
        _emotion = emotion;
        _intensity = intensity;
        _apply_emotion_behavior();
    }

    void _update(Modifiable& stackchan) override
    {
        if (!stackchan.hasAvatar() || stackchan.avatar().isModifyLocked()) {
            return;
        }

        uint32_t now = GetHAL().millis();
        if (now < _next_tick) {
            return;
        }

        perform_emotional_idle(stackchan);

        // 动态调整下次触发间隔（情绪化）
        uint32_t base = 2200;
        if (_emotion == Emotion::Excited || _emotion == Emotion::Surprised) base = 1200;
        if (_emotion == Emotion::Sad || _emotion == Emotion::Sleepy) base = 3800;

        uint32_t delay = static_cast<uint32_t>(Random::getInstance().getInt(base * 0.7f, base * 1.4f));
        _next_tick = now + delay;
    }

private:
    void perform_emotional_idle(Modifiable& stackchan)
    {
        auto& avatar = stackchan.avatar();
        auto& motion = stackchan.motion();
        auto& random = Random::getInstance();

        if (_need_get_home_angles) {
            _home_angles = motion.getCurrentAngles();
            _need_get_home_angles = false;
        }

        int action = random.getInt(0, 100);

        // 根据情绪调整行为概率
        float happy_bias = (_emotion == Emotion::Happy || _emotion == Emotion::Excited) ? 1.3f : 1.0f;

        if (action < static_cast<int>(35 * happy_bias)) {
            // 眼神游离 + 轻微头部姿态
            int offsetX = random.getInt(-35, 35) * _intensity;
            int offsetY = random.getInt(-20, 20) * _intensity;
            avatar.leftEye().setPosition({offsetX, offsetY});
            avatar.rightEye().setPosition({offsetX, offsetY});

            // 轻微点头/歪头（情绪化）
            if (!motion.isMoving() && random.getInt(0, 100) < 40) {
                int yaw_delta   = random.getInt(-25, 25) * _intensity;
                int pitch_delta = random.getInt(-15, 20) * _intensity;
                const auto yaw_limits   = motion.yawServo().getAngleLimit();
                const auto pitch_limits = motion.pitchServo().getAngleLimit();
                const int safe_yaw_min = std::max(yaw_limits.x, _home_angles.x - 25);
                const int safe_yaw_max = std::min(yaw_limits.y, _home_angles.x + 25);
                const int safe_pitch_min = std::max(pitch_limits.x, _home_angles.y);
                const int safe_pitch_max = std::min(pitch_limits.y, _home_angles.y + 20);
                const int target_yaw = uitk::clamp(
                    _home_angles.x + yaw_delta, safe_yaw_min, safe_yaw_max);
                const int target_pitch = uitk::clamp(
                    _home_angles.y + pitch_delta, safe_pitch_min, safe_pitch_max);
                motion.moveWithSpeed(target_yaw, target_pitch, 120);
            }
        } 
        else if (action < 55) {
            // 嘴巴表情（情绪化休息姿势）
            if (_emotion == Emotion::Happy) {
                avatar.mouth().setWeight(random.getInt(15, 35));
            } else if (_emotion == Emotion::Sad) {
                avatar.mouth().setWeight(random.getInt(0, 15));
                avatar.mouth().setRotation(random.getInt(-20, 5));
            } else if (_emotion == Emotion::Curious) {
                avatar.mouth().setWeight(random.getInt(10, 25));
            }
        } 
        else if (action < 70) {
            // 重置到中性（情绪化回归）
            reset_to_emotional_neutral(avatar);
        }
        else {
            // 眨眼或呼吸加强（情绪化）
            // 这里可以触发 blink modifier 或直接操作
        }
    }

    void reset_to_emotional_neutral(avatar::Avatar& avatar)
    {
        avatar.leftEye().setPosition({0, 0});
        avatar.rightEye().setPosition({0, 0});
        avatar.mouth().setPosition({0, 0});
        avatar.mouth().setRotation(0);
        avatar.mouth().setWeight(0);
        avatar.leftEye().setSize(0);
        avatar.rightEye().setSize(0);
    }

    void _apply_emotion_behavior() {
        // 可在此处根据情绪预设眨眼率、头部基准姿态等
    }

    Emotion _emotion = Emotion::Neutral;
    float   _intensity = 0.7f;
    uint32_t _next_tick = 0;
    bool _need_get_home_angles = true;
    uitk::Vector2i _home_angles;
};

}  // namespace stackchan
