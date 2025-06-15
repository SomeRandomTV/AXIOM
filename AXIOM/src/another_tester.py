import pcm
import simpleaudio as sa

pcm_bytes = pcm.tobytes()
wave_obj = sa.WaveObject(pcm_bytes, num_channels=1, bytes_per_sample=2, sample_rate=self.sample_rate)
play_obj = wave_obj.play()    # no internal free until PlayObject is done
play_obj.wait_done()