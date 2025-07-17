![image-20250708190934861](C:\Users\ckc\AppData\Roaming\Typora\typora-user-images\image-20250708190934861.png)

## To do list 7.9:

- add function: Code intepreter . Let users ask math questions or code questions, and then it generates the correct answer or code files, code image using **code_interpreter** tool
- Make the layout.html better, and seperate the QUERY function aside, newly build a query.html, layout.html includes only the Navbar.

## To do list 7.10: 

- function call: Send emails using human languages
- Codex
- Walfram
- **Issue: Mardown in history.html can't be parsed.**

![image-20250711194141867](C:\Users\ckc\AppData\Roaming\Typora\typora-user-images\image-20250711194141867.png)

## Completion 7.10

1. image and file(pdf) inputs

2. Generate images

   **Price**:

   For one 1024*1024 image **input**, it takes about 1024 mutiplies 2.5 tokens , about 2500 tokens to analyse(using gpt-4.1-nano)

   For **output**, see the follows:

   *Likely if I generate one image: 272 / 1 000 000 × $40 ≈ **$0.0109**, I'll spend 0.01$*

   | Quality | Square (1024×1024) | Portrait (1024×1536) | Landscape (1536×1024) |
   | :------ | :----------------- | :------------------- | :-------------------- |
   | Low     | 272 tokens         | 408 tokens           | 400 tokens            |
   | Medium  | 1056 tokens        | 1584 tokens          | 1568 tokens           |
   | High    | 4160 tokens        | 6240 tokens          | 6208 tokens           |

   | Model                  |  Input | Cached input | Output |
   | :--------------------- | -----: | -----------: | -----: |
   | gpt-image-1gpt-image-1 | $10.00 |        $2.50 | $40.00 |

| gpt-4.1gpt-4.1-2025-04-14           | $2.00 | $0.50  | $8.00 |
| :---------------------------------- | ----- | ------ | ----- |
| gpt-4.1-minigpt-4.1-mini-2025-04-14 | $0.40 | $0.10  | $1.60 |
| gpt-4.1-nanogpt-4.1-nano-2025-04-14 | $0.10 | $0.025 | $0.40 |

![image-20250711224726704](C:\Users\ckc\AppData\Roaming\Typora\typora-user-images\image-20250711224726704.png)

3. History successfully allow all the previous image and text![image-20250712003827306](C:\Users\ckc\AppData\Roaming\Typora\typora-user-images\image-20250712003827306.png)

## 7.13 Completion

1. Add web search function. Users can choose it to get the latest news.

2. Optimise the image generation conversation. Now the Image conversation can show users all the messages about the image they generate.

3. History.html adds the picture pharsing function. Now all the pictures in history can be presented correctly.

   ![image-20250713004938939](C:\Users\ckc\AppData\Roaming\Typora\typora-user-images\image-20250713004938939.png)

![image-20250713005008307](C:\Users\ckc\AppData\Roaming\Typora\typora-user-images\image-20250713005008307.png)

**Issue: Markdown still can not be pharsed in history.html**

## 7.14 Completion

1. **FIX ISSUE !! Markdown now can be correctly pharsed in history.html**

![image-20250714141241844](C:\Users\ckc\AppData\Roaming\Typora\typora-user-images\image-20250714141241844.png)

2. Add one function : Code interpreter

   ![image-20250715015153759](C:\Users\ckc\AppData\Roaming\Typora\typora-user-images\image-20250715015153759.png)

It can receive almost every type of files, and generate files you want. 

## 7.15 Test Code Intepreter

![image-20250715180419609](C:\Users\ckc\AppData\Roaming\Typora\typora-user-images\image-20250715180419609.png)

![cfile_68767ae299448191892a3e93ec28fa33](C:\Users\ckc\Desktop\CS50x2024\Project\temp_files\cfile_68767ae299448191892a3e93ec28fa33.png)![cfile_68767ae29a1481919ce35cb52a0c3d0b](C:\Users\ckc\Desktop\CS50x2024\Project\temp_files\cfile_68767ae29a1481919ce35cb52a0c3d0b.png)
