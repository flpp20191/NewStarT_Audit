// Usage example:
// const multiSelect = new MultiSelect('my-multi-select');

class MultiSelect {
    constructor(elementId, conf = {
        placeholder: 'Atlases opcijas',
        search: false,
        radio: false,
    }) {
        this.conf = conf;
        this.selectedOptions = {};
        console.log('MultiSelect initialized with config:', conf);
        this.element = document.getElementById(elementId);
        const name = this.element.getAttribute('name');

        const container = document.createElement('div');
        container.className = 'multi-select';
        this.element.parentNode.insertBefore(container, this.element);
        container.appendChild(this.element);

        const header = document.createElement('div');
        header.className = 'multi-select-header';
        header.textContent = this.conf.placeholder;
        // header.addEventListener('click', () => {
        //     const optionsDiv = container.querySelector('.multi-select-options');
        //     optionsDiv.style.display = optionsDiv.style.display === 'none' ? '' : 'none';
        // });
        container.appendChild(header);

        const multiSelect = document.createElement('div');
        multiSelect.className = 'multi-select-options';
        // multiSelect.style.display = 'none';
        container.appendChild(multiSelect);

        const options = this.element.getElementsByTagName('option');
        for (const option of options) {
            const id = elementId + '_' + option.value;
            const label = document.createElement('label');
            label.dataset.parent = option.dataset.parent;
            label.style.paddingLeft = (option.dataset.depth * 2) + 1 + 'rem';
            multiSelect.appendChild(label);
            label.className = 'multi-select-option';
            
            const checkbox = document.createElement('input');
            label.appendChild(checkbox);
            checkbox.type = (conf.radio) ? "radio" : "checkbox";
            checkbox.name = name;
            if (option.selected) this.selectedOptions[option.value] = option.text;
            checkbox.checked = option.selected;
            checkbox.value = Number(option.value);
            checkbox.dataset.text = option.text;
            checkbox.id = id;
            label.appendChild(document.createTextNode(option.text));
            label.setAttribute('for', id);

            checkbox.addEventListener('change', (e) => {
                this.headerChange(e.target);
            });
        };
        this.element.style.display = 'none';
        this.element.disabled = true;
        this.updateHeader();
    }
    headerChange(checkbox) {
        if (this.conf.radio) this.selectedOptions = {};
        if (checkbox.checked) {
            this.selectedOptions[checkbox.value] = checkbox.dataset.text;
        } else {
            delete this.selectedOptions[checkbox.value];
        }
        this.updateHeader();
    }
    updateHeader() {
        const header = this.element.parentNode.querySelector('.multi-select-header');
        if (Object.keys(this.selectedOptions).length > 0) {
            let result = [];
            for (const key in this.selectedOptions) {
                result.push(this.selectedOptions[key]);
            }
            var x = 0;
            header.textContent = "";
            while (x < 3 && x < result.length) {
                const span = document.createElement('span');
                span.textContent = result[x];
                span.className = 'multi-select-header-item';
                header.appendChild(span);
                x += 1;
            }
            if (result.length > 3) {
                const moreSpan = document.createElement('span');
                moreSpan.textContent = `+${result.length - 3} ` + (result.length - 3 === 1 ? 'cita' : 'citas');
                moreSpan.className = 'multi-select-header-item';
                header.appendChild(moreSpan);
            }
        } else {
            header.textContent = this.conf.placeholder;
        }
    }
}
