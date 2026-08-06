import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { aiApi } from '../../lib/ai'
import { MarkdownText } from '../shared/MarkdownText'
import type { QuizQuestion } from '../../lib/api'

export function QuizPanel({ chapterId }: { chapterId: string }) {
  const [open, setOpen] = useState(false)
  const [index, setIndex] = useState(0)
  const [picked, setPicked] = useState<number | null>(null)
  const [score, setScore] = useState(0)

  const generate = useMutation({
    mutationFn: () => aiApi.generateQuiz(chapterId),
    onSuccess: () => {
      setIndex(0)
      setPicked(null)
      setScore(0)
    },
  })

  function start() {
    setOpen(true)
    generate.mutate()
  }

  function pick(choiceIndex: number, question: QuizQuestion) {
    if (picked !== null) return
    setPicked(choiceIndex)
    if (choiceIndex === question.correct_index) setScore((s) => s + 1)
  }

  function next(total: number) {
    if (index + 1 >= total) {
      setOpen(false)
      return
    }
    setIndex((i) => i + 1)
    setPicked(null)
  }

  if (!open) {
    return (
      <div className="mt-6">
        <h2 className="mb-2 text-sm font-medium text-neutral-400">Study coach</h2>
        <button onClick={start} className="rounded bg-neutral-800 px-3 py-1.5 text-sm hover:bg-neutral-700">
          Quiz me on this chapter
        </button>
      </div>
    )
  }

  return (
    <div className="mt-6">
      <h2 className="mb-2 text-sm font-medium text-neutral-400">Study coach</h2>
      <div className="rounded bg-neutral-900 p-4">
        {generate.isPending && <p className="text-sm text-neutral-600">Writing a quiz from this chapter…</p>}

        {generate.isError && (
          <p className="text-sm text-red-400">
            Couldn't generate a quiz -- check your provider's key in <code className="rounded bg-neutral-950 px-1">.env</code>.
          </p>
        )}

        {generate.data && !generate.data.configured && (
          <p className="text-sm text-neutral-600">
            Not set up yet.{' '}
            <Link to="/settings" className="text-neutral-400 underline decoration-dotted hover:text-neutral-200">
              Add a provider in Settings
            </Link>
            .
          </p>
        )}

        {generate.data?.configured && generate.data.questions.length > 0 && (
          <QuizQuestionView
            question={generate.data.questions[index]}
            questionNumber={index + 1}
            total={generate.data.questions.length}
            picked={picked}
            score={score}
            onPick={(i) => pick(i, generate.data!.questions[index])}
            onNext={() => next(generate.data!.questions.length)}
          />
        )}

        <button onClick={() => setOpen(false)} className="mt-3 text-xs text-neutral-600 hover:text-neutral-400">
          Close
        </button>
      </div>
    </div>
  )
}

function QuizQuestionView({
  question, questionNumber, total, picked, score, onPick, onNext,
}: {
  question: QuizQuestion
  questionNumber: number
  total: number
  picked: number | null
  score: number
  onPick: (index: number) => void
  onNext: () => void
}) {
  return (
    <div>
      <p className="mb-3 text-xs text-neutral-500">
        Question {questionNumber} of {total} &middot; Score: {score}
      </p>
      <p className="mb-3 text-sm">{question.question}</p>
      <div className="flex flex-col gap-1.5">
        {question.choices.map((choice, i) => {
          const isCorrect = i === question.correct_index
          const isPicked = i === picked
          let style = 'border-neutral-700 hover:bg-neutral-800'
          if (picked !== null && isCorrect) style = 'border-green-700 bg-green-950 text-green-200'
          else if (picked !== null && isPicked) style = 'border-red-800 bg-red-950 text-red-200'

          return (
            <button
              key={i}
              onClick={() => onPick(i)}
              disabled={picked !== null}
              className={`rounded border px-3 py-1.5 text-left text-sm ${style}`}
            >
              {choice}
            </button>
          )
        })}
      </div>

      {picked !== null && (
        <div className="mt-3">
          <MarkdownText content={question.explanation} className="text-xs text-neutral-400" />
          <button onClick={onNext} className="mt-2 rounded bg-neutral-800 px-3 py-1 text-sm hover:bg-neutral-700">
            {questionNumber >= total ? 'Finish' : 'Next question'}
          </button>
        </div>
      )}
    </div>
  )
}
