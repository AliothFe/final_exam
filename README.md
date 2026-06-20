# 形势与政策 I 复习答题程序 v2.0.0

这是一个中文图形界面的考前答题程序，题库已全量覆盖 PDF 的主要复习结构：

- 考情概览
- 九个高频专题
- 客观题速记清单
- 主观题答题模板
- 考前背诵优先级建议

功能：

- 支持单选题和多选题
- 支持进阶填空题
- 支持分章节练习
- 支持全部题目打乱练习
- 支持只练基础选择题或只练进阶填空题
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
