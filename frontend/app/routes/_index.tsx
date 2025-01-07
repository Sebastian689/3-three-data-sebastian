import type { MetaFunction, ActionFunctionArgs } from "@remix-run/node";
import { json } from "@remix-run/node"; // or cloudflare/deno
import { useLoaderData } from "@remix-run/react";


export const meta: MetaFunction = () => {
  return [
    { title: "ThreeData" },
    { name: "description", content: "ThreeData" },
  ];
};

const API_ADDRESS = process.env.API_ADDRESS;

export async function loader() {
  const res = await fetch(`${API_ADDRESS}/questions`);
  return json(await res.json());
}

export const action = async ({ request }) => {
  const formData = await request.formData();
  const data = {
    question: formData.get('question'),
    answer1: formData.get('answer1'),
    answer2: formData.get('answer2'),
    answer3: formData.get('answer3'),
    answer4: formData.get('answer4'),
    correct_answer: formData.get('correct_answer'),
  };

  const url = `${API_ADDRESS}/questions`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    console.log(response)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(result);
    return json({ success: true, result });
  } catch (error) {
    return json({ success: false, error: error.message });
  }
};

export default function Index() {
  const questions = useLoaderData<typeof loader>();
  return (
    <div className="prose">
      <div className="flex flex-col items-center gap-16">
        <header className="flex flex-col items-center gap-9">
          <h1 className="leading text-2xl font-bold text-gray-800 dark:text-gray-100">
            ThreeData Questions
          </h1>
          <ul>
            {questions.map((question) => (
              <li key={question.id}>
                <br />
                <h2>{question.question}</h2>
                <ul>
                  <li>1) {question.answer1}</li>
                  <li>2) {question.answer2}</li>
                  <li>3) {question.answer3}</li>
                  <li>4) {question.answer4}</li>
                </ul>
                <div className="relative group">
                  <span className="block text-gray-700 text-sm font-bold mb-2">Correct Answer</span>
                  <span className="hidden group-hover:block absolute bg-white text-black p-2 border rounded shadow-lg">
                    {question.correct_answer}
                  </span>
                </div>

              </li>
            ))}
          </ul>
        </header>
        <h1 className="leading text-2xl font-bold text-gray-800 dark:text-gray-100">
            Add new question
        </h1>
        <form method="post" action="/?index">
          <div>
            <label>
              Question: <input type="text" name="question" />
            </label>
          </div>
          <div>
            <label>
              Answer 1: <input type="text" name="answer1" />
            </label>
          </div>
          <div>
            <label>
              Answer 2: <input type="text" name="answer2" />
            </label>
          </div>
          <div>
            <label>
              Answer 3: <input type="text" name="answer3" />
            </label>
          </div>
          <div>
            <label>
              Answer 4: <input type="text" name="answer4" />
            </label>
          </div>
          <div>
            <label>
              Correct Answer: <input type="int" name="correct_answer" />
            </label>
          </div>
          <button className="btn bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded" type="submit">
            Create
          </button>
        </form>
      </div>
    </div >
  );
}
