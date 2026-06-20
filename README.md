# 形势与政策 I 选择题练习 v1.0.0

这是一个中文图形界面的考前答题程序，题库覆盖 PDF 高频专题一、二：

- 高频专题一：浙大校训精神与求是学子的使命
- 高频专题二：当前国际格局、国家利益与中国特色大国外交

功能：

- 支持单选题和多选题
- 支持重新作答所有题
- 做完一轮后自动生成错题集
- 支持只做错题，并用本轮仍答错的题覆盖原错题集
- 打包后的 exe 自带题库和中文字体，不依赖目标机器的 Python 环境

## 开发运行

```powershell
$env:PYTHONPATH="src"
python -m final_exam_quiz
```

## 打包

```powershell
python -m pip install -r requirements.txt
pyinstaller final_exam_quiz.spec
```

打包产物位于：

```text
dist/FinalExamQuiz.exe
```

错题集运行时保存在 exe 同级目录的：

```text
user_data/mistakes.json
```
