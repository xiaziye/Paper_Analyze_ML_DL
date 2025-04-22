import re

def extract_latex_formulas(latex_text):
    math_environments = {'equation', 'align', 'gather', 'multline', 'eqnarray', 'math', 'displaymath'}

    patterns = [
        # 环境模式（优先匹配）
        (r'\\begin\{([^}]+?)\}(.*?)\\end\{\1\}', True, re.DOTALL),
        # 行间公式 $$
        (r'\$\$(.*?)\$\$', False, re.DOTALL),
        # 行内公式 $
        (r'\$(?!\$)(.*?)(?<!\$)\$', False, 0),  # 排除$$干扰
        # 括号公式 \(...\)
        (r'\\\((.*?)\\\)', False, 0),
        # 方括号公式 \[...\]
        (r'\\\[(.*?)\\\]', False, 0),
    ]

    formulas = []

    for pattern, is_env, flags in patterns:
        regex = re.compile(pattern, flags)
        matches = regex.findall(latex_text)

        for match in matches:
            if is_env:
                env_name, content = match
                env_name = env_name.strip()
                content = content.strip()
                base_env = env_name.rstrip('*')
                if base_env in math_environments and content:  # 过滤空环境
                    formulas.append(content)
            else:
                # 提取内容并过滤空字符串
                formula = match.strip() if isinstance(match, str) else match[0].strip()
                if formula:
                    formulas.append(formula)

    return formulas

# 测试样例
latex_text = r"""
空行间公式：$$$$
正常行间公式：$$ \int_a^b f(x)dx $$
行内公式：$E = mc^2$ 和空行内公式：$ $
方程环境：
\begin{equation}
e^{i\pi} + 1 = 0
\end{equation}
空方程环境：\begin{equation}\end{equation}
括号公式：\(\sum_{n=1}^\infty \frac{1}{n^2}\)
"""

formulas = extract_latex_formulas(latex_text)
for i, formula in enumerate(formulas, 1):
    print(f"公式{i}: {formula}")
