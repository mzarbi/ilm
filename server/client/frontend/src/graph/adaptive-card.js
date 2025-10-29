import * as joint from 'jointjs';
import { HostConfig, AdaptiveCard, SubmitAction, OpenUrlAction } from 'adaptivecards';


console.log('AdaptiveCards?', window.AdaptiveCards);

const AC_MARKUP = [
  {
    tagName: 'foreignObject',
    selector: 'fo',
    attributes: { requiredExtensions: 'http://www.w3.org/1999/xhtml' },
    children: [
      {
        namespaceURI: 'http://www.w3.org/1999/xhtml',
        tagName: 'div',
        selector: 'content',
        style: { width: '100%', height: '100%', overflow: 'hidden' }
      }
    ]
  }
];

const Flags = {
  Render: '@render-view',
  Update: '@update-view',
  Transform: '@transform-view',
  Measure: '@measure-view',
};

const hostConfig = new HostConfig({
    fontFamily: 'Segoe UI, Helvetica Neue, sans-serif',
    containerStyles: {
        default: {
            backgroundColor: '#FFFFFF',
            foregroundColors: {
                default: {
                    default: '#333333',
                    subtle: '#484644',
                },
                accent: {
                    default: '#2E89FC',
                    subtle: '#0078D4'
                },
                attention: {
                    default: '#D13438',
                    subtle: '#A4262C'
                },
                dark: {
                    default: '#000000',
                    subtle: '#646464'
                },
                good: {
                    default: '#0B6A0B',
                    subtle: '#028A02'
                },
                light: {
                    default: '#FFFFFF',
                    subtle: '#E6E6E6'
                },
                warning: {
                    default: '#B75C00',
                    subtle: '#986F0B'
                }
            }
        },
        emphasis: {
            backgroundColor: '#F2F2F2',
            foregroundColors: {
                default: {
                    default: '#000000',
                    subtle: '#484644'
                }
            }
        },
        accent: {
            backgroundColor: '#C7DEF9',
            foregroundColors: {
                default: {
                    default: '#333333',
                    subtle: '#484644'
                }
            }
        },
        good: {
            backgroundColor: '#CCFFCC',
            foregroundColors: {
                default: {
                    default: '#333333',
                    subtle: '#484644'
                }
            }
        },
        attention: {
            backgroundColor: '#FFC5B2',
            foregroundColors: {
                default: {
                    default: '#333333',
                    subtle: '#484644'
                }
            }
        },
        warning: {
            backgroundColor: '#FFE2B2',
            foregroundColors: {
                default: {
                    default: '#333333',
                    subtle: '#484644'
                }
            }
        }
    },
    supportsInteractivity: true,
    imageSizes: {
        small: 40,
        medium: 80,
        large: 160
    },
    actions: {
        actionAlignment: 'stretch',
        actionsOrientation: 'vertical',
        buttonSpacing: 8,
        maxActions: 100,
        showCard: {
            actionMode: 'inline',
            inlineTopMargin: 8
        },
        spacing: 'default'
    },
    adaptiveCard: {
        allowCustomStyle: false
    },
    imageSet: {
        imageSize: 'medium',
        maxImageHeight: 100
    },
    factSet: {
        title: {
            color: 'default',
            size: 'default',
            isSubtle: false,
            weight: 'bolder',
            wrap: true,
            maxWidth: 150
        },
        value: {
            color: 'default',
            size: 'default',
            isSubtle: false,
            weight: 'default',
            wrap: true
        },
        spacing: 8
    },
    textBlock: {
        headingLevel: 1
    }
});

/* ----------------- MODEL with MARKUP ----------------- */
export const AdaptiveCardModel = joint.dia.Element.define(
  'app.AdaptiveCardModel',
  {
    size: { width: 300, height: 60 },
    template: null,
    border: '2px solid #ddd',
  },
  {
    markup: AC_MARKUP,   // <<< put it here
  }
);

// ✅ NAMED export
export const AdaptiveCardModelView = joint.dia.ElementView.extend({
  presentationAttributes: {
    size: [Flags.Update],
    position: [Flags.Transform],
    angle: [Flags.Transform],
    template: [Flags.Render],
    border: [Flags.Update],
  },

  initFlag: [Flags.Render, Flags.Update, Flags.Transform, Flags.Measure],

  init() {
    const card = new AdaptiveCard();
    card.hostConfig = hostConfig;
    card.onExecuteAction = (a) => {
      if (a instanceof SubmitAction) this.notify('element:submit', a.data);
      if (a instanceof OpenUrlAction) this.notify('element:open-url', a.url);
    };
    this.card = card;
    this.ro = new ResizeObserver(() => this.requestUpdate(this.getFlag(Flags.Measure)));
    this.foEl = null;
    this.contentEl = null;
  },

  render() {
    // build DOM from model.markup (already set)
    joint.dia.ElementView.prototype.render.apply(this, arguments);

    // cache nodes created by base render
    this.foEl = this.findBySelector('fo')[0] || null;
    this.contentEl = this.findBySelector('content')[0] || null;
    if (!this.foEl || !this.contentEl) return this;

    // ensure non-zero box on first paint
    const { width, height } = this.model.size();
    this.foEl.setAttribute('width', width || 300);
    this.foEl.setAttribute('height', height || 60);

    // initial placeholder and actual Adaptive Card
    this.contentEl.innerHTML = '<div style="padding:8px;font:14px/1.2 sans-serif">[AC loading…]</div>';

    try {
      const tmpl = this.model.get('template') || { type: 'AdaptiveCard', version: '1.5', body: [] };
      this.card.parse(tmpl);
      const node = this.card.render();

      this.contentEl.innerHTML = '';
      this.contentEl.appendChild(node);

      node.style.boxSizing = 'border-box';
      node.style.width = '100%';
      node.style.minHeight = '40px';
      node.style.border = this.model.get('border') || '2px solid #ddd';

      this.ro.observe(node);
    } catch (e) {
      this.contentEl.innerHTML =
        `<div style="padding:8px;color:#b00020;font:12px/1.3 monospace">AC error: ${String(e)}</div>`;
    }

    return this;
  },

  confirmUpdate(flags) {
    if (this.hasFlag(flags, Flags.Render)) this.render();
    if (this.hasFlag(flags, Flags.Update)) this.update();
    if (this.hasFlag(flags, Flags.Transform)) this.updateTransformation();
    if (this.hasFlag(flags, Flags.Measure)) this._resizeModelToCard();
  },

  _resizeModelToCard() {
    const el = this.card.renderedElement;
    if (!el) return;
    const { width, height } = this.model.size();
    const nextH = el.offsetHeight || 0;
    if (height !== nextH) {
      this.model.resize(width, nextH, { view: this.cid });
      this.update();
    }
  },

  update() {
    if (!this.foEl) return;
    const { width, height } = this.model.size();
    this.foEl.setAttribute('width', width);
    this.foEl.setAttribute('height', height);
    if (this.card.renderedElement) {
      this.card.renderedElement.style.border = this.model.get('border') || '2px solid #ddd';
      this.card.renderedElement.style.boxSizing = 'border-box';
      this.card.renderedElement.style.width = '100%';
    }
    this.cleanNodesCache();
  },

  onRemove() {
    this.ro?.disconnect?.();
    this.card?.releaseDOMResources?.();
  }
});

/* register by name + ensure namespace used by Paper */
joint.shapes.app = joint.shapes.app || {};
joint.shapes.app.AdaptiveCardModelView = AdaptiveCardModelView;
