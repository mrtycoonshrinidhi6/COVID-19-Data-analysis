import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

export function AnimatedCounter({ from = 0, to, duration = 2, format = 'number' }) {
  const [count, setCount] = useState(from)

  useEffect(() => {
    if (to === undefined || to === null) {
      setCount(0)
      return
    }

    const startTime = Date.now()
    const diff = to - from
    const frameRate = 60
    const totalFrames = (duration * 1000) / (1000 / frameRate)
    let frame = 0

    const timer = setInterval(() => {
      frame++
      const progress = Math.min(frame / totalFrames, 1)
      // Easing function for smooth animation
      const easeProgress = 1 - Math.pow(1 - progress, 3)
      setCount(Math.floor(from + diff * easeProgress))

      if (progress >= 1) {
        clearInterval(timer)
        setCount(to)
      }
    }, 1000 / frameRate)

    return () => clearInterval(timer)
  }, [to, from, duration])

  return (
    <motion.span
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      {count.toLocaleString()}
    </motion.span>
  )
}
