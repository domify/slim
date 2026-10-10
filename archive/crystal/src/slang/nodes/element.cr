module Slang
  module Nodes
    class Element < Node
      SELF_CLOSING_TAGS = %w{area base br col embed hr img input keygen link menuitem meta param source track wbr}
      RAW_TEXT_TAGS     = %w(script style)

      delegate :name, :attributes, to: @token

      def self_closing?
        SELF_CLOSING_TAGS.includes?(name)
      end

      def allow_children_to_escape?
        !RAW_TEXT_TAGS.includes?(name)
      end

      def to_s(str, buffer_name)
        str << "#{buffer_name} << \" \"\n" if prepend_whitespace
        str << "#{buffer_name} << \"<#{name}\"\n"
        if (attribute = select_attributes.find(&.id?))
          str << "#{buffer_name} << \" id=\\\"\"\n"
          if attribute.escaped
            str << "::HTML.escape((#{attribute.value}).to_s, #{buffer_name})\n"
          else
            str << "(#{attribute.value}).to_s(#{buffer_name})\n"
          end
          str << "#{buffer_name} << \"\\\"\"\n"
        end
        # handle class attribute merging
        class_attributes = select_attributes.select(&.class?)
        if (splat_var = @token.splat)
          str << "::Slang.let((#{splat_var})[\"class\"]?) do |__splat_class__|\n"
          str << "if !#{class_attributes.empty?} || __splat_class__\n"
          str << "#{buffer_name} << \" class=\\\"\"\n"
          str << "__first_class__ = true\n"
          class_attributes.each do |attribute|
            str << "::Slang.let(#{attribute.value}) do |__value__|\n"
            str << "if __value__.to_s.presence\n"
            str << "#{buffer_name} << \" \" unless __first_class__\n"
            str << "__first_class__ = false\n"
            if attribute.escaped
              str << "::HTML.escape(__value__.to_s, #{buffer_name})\n"
            else
              str << "__value__.to_s(#{buffer_name})\n"
            end
            str << "end\n"
            str << "end\n"
          end
          str << "if __splat_class__\n"
          str << "#{buffer_name} << \" \" unless __first_class__\n"
          str << "::HTML.escape(__splat_class__.to_s, #{buffer_name})\n"
          str << "end\n"
          str << "#{buffer_name} << \"\\\"\"\n"
          str << "end\n"
          str << "end\n"
        elsif !class_attributes.empty?
          str << "#{buffer_name} << \" class=\\\"\"\n"
          class_attributes.each_with_index do |attribute, i|
            str << "::Slang.let(#{attribute.value}) do |__value__|\n"
            str << "if __value__.to_s.presence\n"
            str << "#{buffer_name} << \" \"\n" if i > 0
            if attribute.escaped
              str << "::HTML.escape(__value__.to_s, #{buffer_name})\n"
            else
              str << "__value__.to_s(#{buffer_name})\n"
            end
            str << "end\n"
            str << "end\n"
          end
          str << "#{buffer_name} << \"\\\"\"\n"
        end
        select_attributes.reject(&.id_or_class?).each do |attribute|
          # remove the attribute if value evaluates to false
          # remove the value if value evaluates to true
          str << "::Slang.let(#{attribute.value}) do |__value__|\n"
          str << "unless __value__ == false\n"
          str << "#{buffer_name} << \" #{attribute.name}\"\n"
          str << "unless __value__ == true\n"
          str << "#{buffer_name} << \"=\\\"\"\n"
          if attribute.escaped
            str << "::HTML.escape(__value__.to_s, #{buffer_name})\n"
          else
            str << "(__value__).to_s(#{buffer_name})\n"
          end
          str << "#{buffer_name} << \"\\\"\"\n"
          str << "end\n"
          str << "end\n"
          str << "end\n"
        end
        if (splat_var = @token.splat)
          str << "(#{splat_var}).each do |__key__, __value__|\n"
          str << "next if __key__ == \"class\"\n"
          str << "#{buffer_name} << \" \"\n"
          str << "#{buffer_name} << __key__\n"
          str << "#{buffer_name} << \"=\\\"\"\n"
          str << "::HTML.escape(__value__.to_s, #{buffer_name})\n"
          str << "#{buffer_name} << \"\\\"\"\n"
          str << "end\n"
        end
        str << "#{buffer_name} << \">\"\n"
        if children?
          nodes.each do |node|
            node.to_s(str, buffer_name)
          end
        end
        if !self_closing?
          str << "#{buffer_name} << \"</#{name}>\"\n"
        end
        str << "#{buffer_name} << \" \"\n" if append_whitespace
      end

      private def select_attributes
        nodes.select(Attribute)
      end
    end
  end
end
