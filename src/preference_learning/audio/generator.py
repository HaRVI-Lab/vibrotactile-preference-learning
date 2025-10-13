"""
Audio signal generation and playback utilities.
"""

from __future__ import annotations

import os
import tempfile
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, Tuple

import numpy as np
from scipy.io import wavfile

from .signal import generate_tone_signal

try:
    import pygame

    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False

try:
    import sounddevice as sd

    SOUNDDEVICE_AVAILABLE = True
except Exception:
    SOUNDDEVICE_AVAILABLE = False


ParameterRanges = Dict[str, Tuple[float, float]]


@dataclass
class AudioGenerator:
    """Generate and play audio signals for preference learning."""

    duration: int = 4
    cycles: int = 1
    sample_rate: int = 44100
    param_ranges: ParameterRanges = field(
        default_factory=lambda: {
            "amplitude": (30.0, 60.0),
            "frequency": (25.0, 75.0),
            "density": (10.0, 90.0),
            "gradient": (-50.0, 50.0),
        }
    )

    def __post_init__(self) -> None:
        self.audio_backend: Optional[str] = None
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(
                    frequency=self.sample_rate,
                    size=-16,
                    channels=1,
                    buffer=512,
                )
                self.audio_backend = "pygame"
            except Exception:
                self.audio_backend = None
        elif SOUNDDEVICE_AVAILABLE:
            self.audio_backend = "sounddevice"

    # ------------------------------------------------------------------ #
    # Signal synthesis
    # ------------------------------------------------------------------ #
    def generate_signal(self, amplitude: float, frequency: float, density: float, gradient: float):
        """Generate an audio signal with the provided parameters."""
        amplitude = np.clip(amplitude, *self.param_ranges["amplitude"])
        frequency = np.clip(frequency, *self.param_ranges["frequency"])
        density = np.clip(density, *self.param_ranges["density"])
        gradient = np.clip(gradient, *self.param_ranges["gradient"])

        time_vector, data, for_plot = generate_tone_signal(
            filler_amplitude=amplitude,
            filler_frequency=frequency,
            filler_density=density,
            filler_env_gradient=gradient,
            duration=self.duration,
            cycles=self.cycles,
            fs=self.sample_rate,
        )

        max_abs = np.max(np.abs(data))
        if max_abs > 0:
            data = data / max_abs * 0.8

        metadata = {
            "parameters": {
                "amplitude": amplitude,
                "frequency": frequency,
                "density": density,
                "gradient": gradient,
            },
            "duration": self.duration,
            "fs": self.sample_rate,
            "for_plot": for_plot,
        }
        return time_vector, data, metadata

    # ------------------------------------------------------------------ #
    # Persistence helpers
    # ------------------------------------------------------------------ #
    def save_audio(self, data: np.ndarray, filename: Optional[str] = None) -> str:
        """Persist audio data as a WAV file."""
        target = filename
        if target is None:
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            target = temp_file.name
            temp_file.close()

        audio_int16 = (data * 32767).astype(np.int16)
        wavfile.write(target, self.sample_rate, audio_int16)
        return target

    # ------------------------------------------------------------------ #
    # Playback
    # ------------------------------------------------------------------ #
    def play_audio(self, data: np.ndarray, blocking: bool = True) -> bool:
        """Play audio using the available backend."""
        if self.audio_backend is None:
            print("Warning: no audio backend available.")
            return False

        try:
            if self.audio_backend == "pygame":
                return self._play_pygame(data, blocking)
            if self.audio_backend == "sounddevice":
                return self._play_sounddevice(data, blocking)
        except Exception as exc:
            print(f"Audio playback error: {exc}")
            return False
        return False

    def _play_pygame(self, data: np.ndarray, blocking: bool) -> bool:
        temp_file = self.save_audio(data)
        try:
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            if blocking:
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            return True
        finally:
            try:
                os.unlink(temp_file)
            except Exception:
                pass

    def _play_sounddevice(self, data: np.ndarray, blocking: bool) -> bool:
        try:
            sd.play(data, self.sample_rate)
            if blocking:
                sd.wait()
            return True
        except Exception as exc:
            print(f"Sounddevice playback error: {exc}")
            return False

    def stop_audio(self) -> None:
        """Stop any current playback."""
        try:
            if self.audio_backend == "pygame":
                pygame.mixer.music.stop()
            elif self.audio_backend == "sounddevice":
                sd.stop()
        except Exception:
            pass

    def close(self) -> None:
        """Release audio device resources."""
        try:
            if self.audio_backend == "pygame":
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            elif self.audio_backend == "sounddevice":
                sd.stop()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Feature extraction
    # ------------------------------------------------------------------ #
    def calculate_audio_features(self, data: np.ndarray) -> Dict[str, float]:
        """Calculate simple audio features for preference evaluation."""
        features = {
            "rms": float(np.sqrt(np.mean(data**2))),
            "peak": float(np.max(np.abs(data))),
            "energy": float(np.sum(data**2)),
        }

        zero_crossings = np.where(np.diff(np.signbit(data)))[0]
        features["zero_crossing_rate"] = len(zero_crossings) / len(data)

        fft = np.fft.fft(data)
        freqs = np.fft.fftfreq(len(data), 1 / self.sample_rate)
        magnitude = np.abs(fft)
        half = len(magnitude) // 2
        peak_idx = int(np.argmax(magnitude[:half]))
        features["peak_frequency"] = float(freqs[peak_idx])
        features["spectral_centroid"] = float(
            np.sum(freqs[:half] * magnitude[:half]) / np.sum(magnitude[:half])
        )
        return features
