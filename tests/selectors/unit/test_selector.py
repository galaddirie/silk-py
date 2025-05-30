import pytest
from expression import Error, Ok

from silk.selectors.selector import (
    Selector,
    SelectorGroup,
    SelectorType,
    css,
    text,
    xpath,
)


class TestSelector:
    def test_selector_create(self):
        selector = Selector(type=SelectorType.CSS, value=".my-class")

        assert selector.type == SelectorType.CSS
        assert selector.value == ".my-class"
        assert selector.timeout is None

    def test_selector_methods(self):
        selector = Selector(type=SelectorType.CSS, value=".my-class", timeout=10)

        assert selector.get_type() == SelectorType.CSS
        assert selector.get_value() == ".my-class"
        assert selector.get_timeout() == 10
        assert selector.is_css() is True
        assert selector.is_xpath() is False

    def test_selector_string_representation(self):
        selector = Selector(type=SelectorType.CSS, value=".my-class")

        assert str(selector) == "css-.my-class"
        assert repr(selector) == "Selector(type=SelectorType.CSS, value=.my-class)"

    def test_specialized_selectors(self):
        css_selector = css(".my-class")
        xpath_selector = xpath("//div[@class='my-class']")
        text_selector = text("Find me")

        assert css_selector.type == SelectorType.CSS
        assert css_selector.value == ".my-class"

        assert xpath_selector.type == SelectorType.XPATH
        assert xpath_selector.value == "//div[@class='my-class']"

        assert text_selector.type == SelectorType.TEXT
        assert text_selector.value == "Find me"


class TestSelectorGroup:
    def test_selector_group_constructor(self):
        selector1 = css(".class1")
        selector2 = xpath("//div[@id='id1']")

        group = SelectorGroup("test-group", selector1, selector2)

        assert group.name == "test-group"
        assert len(group.selectors) == 2
        assert group.selectors[0] == selector1
        assert group.selectors[1] == selector2

    def test_selector_group_create(self):
        selector1 = css(".class1")
        selector2 = xpath("//div[@id='id1']")

        group = SelectorGroup("test-group", selector1, selector2)

        assert group.name == "test-group"
        assert len(group.selectors) == 2
        assert group.selectors[0] == selector1
        assert group.selectors[1] == selector2

    def test_selector_group_create_mixed(self):
        group = SelectorGroup(
            "mixed-group",
            css(".class1"),
            ".class2",
            ("//div[@id='id1']", "xpath"),
            ("Button text", SelectorType.TEXT),
        )

        assert group.name == "mixed-group"
        assert len(group.selectors) == 4

        assert group.selectors[0].type == SelectorType.CSS
        assert group.selectors[0].value == ".class1"

        assert group.selectors[1].type == SelectorType.CSS
        assert group.selectors[1].value == ".class2"

        assert group.selectors[2].type == SelectorType.XPATH
        assert group.selectors[2].value == "//div[@id='id1']"

        assert group.selectors[3].type == SelectorType.TEXT
        assert group.selectors[3].value == "Button text"

    @pytest.mark.asyncio
    async def test_selector_group_execute(self):
        selector1 = css(".not-found")
        selector2 = xpath("//div[@id='found']")

        group = SelectorGroup("test-group", selector1, selector2)

        async def mock_find_element(selector: Selector):
            if selector.value == ".not-found":
                return Error(Exception("Element not found"))
            else:
                return Ok("Found element")

        result = await group.execute(mock_find_element)

        assert result.is_ok()
        value = result.default_value(None)
        assert value == "Found element"

    @pytest.mark.asyncio
    async def test_selector_group_execute_all_fail(self):
        selector1 = css(".not-found1")
        selector2 = css(".not-found2")

        group = SelectorGroup("test-group", selector1, selector2)

        async def mock_find_element(selector: Selector):
            return Error(Exception("Element not found"))

        result = await group.execute(mock_find_element)

        assert result.is_error()
        assert "All selectors in group 'test-group' failed" in str(result.error)
