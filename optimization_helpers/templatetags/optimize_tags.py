import copy
import os
import json
from django import template
from django.conf import settings
from django.utils.timezone import now
from django.db.models.query import QuerySet

register = template.Library()


def dump_to_json_file(given, file_name="dashboard"):
    path = os.path.expanduser(
        settings.LOCAL_TESTING_DUMPS_PATH if hasattr(settings, "LOCAL_TESTING_DUMPS_PATH") else "~/temp/dump_to_json"
    )
    if settings.LOCAL_TESTING:
        data = json.dumps(given, default=lambda o: o.__dict__, indent=4)
        path_full = os.path.join(path, "{}.json".format(file_name.replace(".json", "")))
        if os.path.exists(path):
            with open(path_full, "w") as out:
                out.write(data)
        else:
            raise Exception("{} - path not exists.".format(path))


@register.simple_tag(takes_context=True)
def optimize_fornode(context, context_variables, template_name, optimize_suffix=None):
    def context_queryset(context, context_variables):
        queryset = None
        for var in context_variables.split("."):
            if queryset:
                queryset = queryset.get(var)
            else:
                queryset = context.get(var)
        return queryset

    time_start = now()
    context_queryset_res = context_queryset(context, context_variables)
    if isinstance(context_queryset_res, QuerySet):
        queryset = copy.copy(context_queryset_res)
        queryset_optimized = optimize(
            template_name=template_name,
            for_item=None,
            context=context,
            context_variables=context_variables,
            queryset=queryset,
            optimize_suffix=optimize_suffix
        )
        if queryset_optimized:
            # context_queryset_res_2 = context_queryset(context, context_variables)
            # context_queryset_res_2 = queryset_optimized
            # TODO ofc should be "dynamic"
            context_variables_list = context_variables.split(".")
            if len(context_variables_list) == 3:
                k1, k2, k3 = context_variables_list
                context[k1][k2][k3] = queryset_optimized
            elif len(context_variables_list) == 2:
                k1, k2 = context_variables_list
                context[k1][k2] = queryset_optimized
            elif len(context_variables_list) == 1:
                k1 = context_variables_list[0]
                context[k1] = queryset_optimized
            else:
                raise Exception("Context!!!")
    else:
        if settings.DEBUG:
            raise Exception("{} not in context".format(context_variables))

    time_end = now() - time_start
    print("OPTIMIZATION {} = {} seconds.".format(context_variables, str(time_end).split(":")[-1]))


def optimize(template_name, for_item, context, context_variables, queryset=None, optimize_suffix=None):
    from django.template.loader import get_template
    from django.template.defaulttags import IfNode, ForNode, SpacelessNode, LoadNode, WithNode
    from django.template.base import TextNode, VariableNode
    from django.template.loader_tags import IncludeNode, ExtendsNode, BlockNode

    def get_file_name(name):
        return "optimize-{}".format(name) + ("-{}".format(optimize_suffix) if optimize_suffix else "")

    def look_for_fornode(nodelist):
        look_for_result = []
        for node in nodelist:
            if isinstance(node, ForNode):
                if str(node.sequence.var) == context_variables:
                    look_for_result.append(node)
            elif isinstance(node, IfNode):
                for condition, nodes in node.conditions_nodelists:
                    # conditions.append(
                    #     condition.text if hasattr(condition, "text") else condition.first.text
                    # )
                    res = look_for_fornode(nodes)
                    if res:
                        look_for_result.append(res)
        if len(look_for_result) > 1:
            raise Exception("Multiple ForNodes with with '{}'".format(context_variables))
        elif look_for_result:
            return look_for_result[0]

    def get_nodes_from_template_name(template_name):
        tmpl = get_template(template_name)
        nodelist = tmpl.template.nodelist
        if isinstance(nodelist[0], ExtendsNode):
            nodelist_obj = nodelist[0].nodelist
            nodelist_list = []
            for node in nodelist_obj:
                if isinstance(node, BlockNode):
                    for node2 in node.nodelist:
                        nodelist_list.append(node2)
                else:
                    nodelist_list.append(node)
            return nodelist_list
        else:
            return tmpl.template.nodelist

    def condition_as_text(condition):
        def get_items(given_obj):
            for aaa in ["first", "second"]:
                if hasattr(given_obj, aaa):
                    aaa_object = getattr(given_obj, aaa)
                    if aaa == ("second" if hasattr(given_obj, "second") and given_obj.second else "first"):
                        eee = str(given_obj).split("(")
                        fff = eee[1]
                        if len(eee) > 2:
                            items.append(fff.strip())
                        else:
                            dump_to_json_file(given_obj, get_file_name("given_obj"))
                    if hasattr(aaa_object, "text"):
                        items.append(aaa_object.text)
                    else:
                        get_items(aaa_object)

            # dump_to_json_file(given_obj, get_file_name("eee"))

        items = []
        get_items(condition)
        return " ".join(items)
        # return str(condition) + "--" + " ".join(items)

    def bool_instead_of_render(ifnode, context):
        """
        https://github.com/django/django/blob/129583a0d3cf69b08d058cd751d777588801b7ad/django/template/defaulttags.py#L298
        """
        for condition, nodelist in ifnode.conditions_nodelists:
            if condition is not None:  # if / elif clause
                try:
                    match = condition.eval(context)
                except e:
                    match = None
            else:  # else clause
                match = True
            return match or False
            # return match

        return ""

    def second_step(fornode, level, conditions_for_level):
        ommit_object = True
        level += 1
        conditions_for_level = conditions_for_level
        result = dict(conditions=[], other_nodes=[], level=level, conditions_for_level=conditions_for_level)
        nodes = fornode.nodelist_loop if hasattr(fornode, "nodelist_loop") else fornode
        for node in nodes:
            if type(node) not in node_types:
                node_types.append(type(node))

            if isinstance(node, IncludeNode):
                nodes2 = get_nodes_from_template_name(node.template.token.replace("'", ""))
                condition_and_children = dict(
                    condition_text="", condition_object=None, children=second_step(nodes2, level, conditions_for_level)
                )
                globals()["general_result"] = condition_and_children
                # dump_to_json_file(condition_and_children, get_file_name("condition_and_children"))
                result["conditions"].append(condition_and_children)
            elif isinstance(node, SpacelessNode):
                condition_and_children = dict(
                    condition_text="",
                    condition_object=None,
                    children=second_step(node.nodelist, level, conditions_for_level),
                )
                globals()["general_result"] = condition_and_children
                # dump_to_json_file(condition_and_children, get_file_name("condition_and_children"))
                result["conditions"].append(condition_and_children)
            elif isinstance(node, WithNode):
                for var, filter_expression in node.extra_context.items():
                    fake_sequence = (
                        [var],
                        (filter_expression.token,)
                    )
                    # raise Exception(node, var, filter_expression, fake_sequence)
                    sequences.append(fake_sequence)
                # lookups_from_filterexpression(lookups, node)
                condition_and_children = dict(
                    condition_text="",
                    condition_object=None,
                    children=second_step(node.nodelist, level, conditions_for_level),
                )
                globals()["general_result"] = condition_and_children
                # dump_to_json_file(condition_and_children, get_file_name("condition_and_children"))
                result["conditions"].append(condition_and_children)
            elif isinstance(node, ForNode):
                if hasattr(node, "sequence"):
                    a = node.loopvars
                    b = node.sequence.var.lookups
                    sequences.append((a, b))
                lookups_from_filterexpression(lookups, node)
                if hasattr(node, "args"):
                    raise Exception("Sahara - we didn t checked that code will be work here")
                    for arg in node.args:
                        lookups_from_filterexpression(lookups, arg)
                condition_and_children = dict(
                    condition_text="",
                    condition_object=None,
                    children=second_step(node.nodelist_loop, level, conditions_for_level),
                )
                globals()["general_result"] = condition_and_children
                # dump_to_json_file(condition_and_children, get_file_name("condition_and_children"))
                result["conditions"].append(condition_and_children)
            elif isinstance(node, IfNode):
                for condition, nodes3 in node.conditions_nodelists:
                    if condition:
                        if hasattr(condition, "first") and condition.first:
                            condition.first.string = str(condition.first)
                        if hasattr(condition, "second") and condition.second:
                            condition.second.string = str(condition.second)
                    if condition_as_text(condition):
                        # raise Exception(
                        #     bool_instead_of_render(node,context),
                        #     condition
                        # )
                        conditions_for_level.append(condition_as_text(condition))

                    condition_block_propagation = (
                        True if (bool_instead_of_render(node, context) if condition else "eeee") is False else None
                    )
                    # if level >= 11:
                    if condition_block_propagation:
                        # TODO remove that if after changes
                        print("PROPAGATION_BLOCKING....BLOCKED!!!! ;)")
                        condition_block_propagation = False
                        # raise Exception(node)
                    if not condition_block_propagation:
                        condition_and_children = dict(
                            condition_text=condition_as_text(condition),
                            condition_object=condition if not ommit_object else str(condition),
                            condition_block_propagation=condition_block_propagation,
                            children=second_step(nodes3, level, conditions_for_level),
                        )
                        show_me_item_with_dots.append((len(show_me_item_with_dots), condition))
                        globals()["general_result"] = condition_and_children
                        # dump_to_json_file(condition_and_children, get_file_name("condition_and_children"))
                        result["conditions"].append(condition_and_children)
            elif isinstance(node, (TextNode, LoadNode)):
                pass
            else:
                result["other_nodes"].append(str(node))
                lookups_from_filterexpression(lookups, node)
                # TODO we need to sequences belove lookups
                if hasattr(node, "args"):
                    for arg in node.args:
                        lookups_from_filterexpression(lookups, arg)

                show_me_item_with_dots.append((len(show_me_item_with_dots), node))
                # raise Exception('fsdadsk')
            dump_to_json_file(result, get_file_name("last_one_maybe"))
        return result

    def lookups_from_filterexpression(lookups, node):
        if hasattr(node, "filter_expression") or hasattr(node, "sequence"):
            filter_expression = node.filter_expression if not hasattr(node, "sequence") else node.sequence
            lookups.append(filter_expression.var.lookups)
            for nfilter in filter_expression.filters:
                for e in nfilter[1]:
                    if hasattr(e[1], "lookups"):
                        lookups.append(e[1].lookups)

    def get_object_from_queryset(queryset):
        if isinstance(queryset, QuerySet):
            return queryset.model
        else:
            raise Exception("Not a queryset. {}".format(type(queryset)))

    def get_lookups_map(lookups):
        lookups_map = dict()
        for list_item in lookups:
            current = lookups_map
            if add_double_underscore_str:
                list_item = list(list_item)
                list_item.append("__str__")
                list_item = tuple(list_item)
            for lookup_item in list_item:
                if lookup_item not in current:
                    current[lookup_item] = dict()
                current = current[lookup_item]
        return lookups_map

    def merge_lookups_using_sequences(lookups):
        def merge_lookup(lookup, keys):
            lookup_before = lookup
            first = lookup[0]
            if first in keys:
                lookup = tuple(list(sequences_as_dict[first]) + list(lookup)[1:])
                keys.remove(lookup_before[0])
                if keys:
                    lookup = merge_lookup(lookup, keys)
            return lookup

        sequences_as_dict = {seq[0][0 if len(seq[0]) == 1 else None]: seq[1] for seq in sequences}
        new = []
        for lookup in lookups:
            lookup = merge_lookup(lookup, list(sequences_as_dict.keys()))
            new.append(lookup)
        return new

    def get_relations(lookups_map, model, variable):
        result = dict(
            relations_to_select=[],
            relations_to_prefetch=[],
            relations_unknown=[],  # i.e. functions
            annotates_to_annotate=[],
            annotates_to_ommit=[],
            other=dict(a=[], b=[], c=[]),
            only_id_and_eee=[],
        )

        def choose_relation_from_related_models(field, model_above):
            """
            we need to choose which related_model from "dostępny" is what we need to use
            """
            related_model = field.rel.related_model if hasattr(field, "rel") else field.field.related_model
            field_rel__related_model = field.rel.related_model if hasattr(field, "rel") else None
            field_field__related_model = field.field.related_model
            if field_rel__related_model and field_field__related_model:
                related_model = (
                    field_field__related_model if field_rel__related_model is model_above else field_rel__related_model
                )
            else:
                related_model = field_rel__related_model or field_field__related_model

            return related_model

        def get_1relation(model, key, glu, relation, prefetch=False):
            relation = relation.copy()
            relation.append(key)

            if hasattr(model, key):
                field = getattr(model, key)
                if((hasattr(field, "field") and hasattr(field.field, "related_model") and field.field.related_model)
                   or hasattr(field, "related")):
                    if hasattr(field, "related"):
                        # django.db.models.fields.related_descriptors.ReverseOneToOneDescriptor
                        related_model = field.related.field.model
                    else:
                        related_model = choose_relation_from_related_models(field=field, model_above=model)
                        prefetch = prefetch or hasattr(field, "rel")

                    for key2, value2 in glu.items():
                        get_1relation(related_model, key2, value2, relation, prefetch=prefetch)
                    else:
                        if prefetch:
                            result["relations_to_prefetch"].append(relation)
                        else:
                            result["relations_to_select"].append(relation)
                elif hasattr(field, "_optimize_related") and field._optimize_related:
                    to_select = field._optimize_related.get("select_related", "").split("__")
                    to_prefetch = field._optimize_related.get("prefetch_related", "").split("__")
                    to_annotate = field._optimize_related.get("annotate", "").split(",")
                    if add_double_underscore_str and key == "__str__":
                        # trick for __str__
                        to_select = relation[:-1] + to_select if to_select[0] else to_select
                        to_prefetch = relation[:-1] + to_prefetch if to_prefetch[0] else to_prefetch

                    if to_select and to_select[0]:
                        result["relations_to_select"].append(to_select)
                    if to_prefetch and to_prefetch[0]:
                        result["relations_to_prefetch"].append(to_prefetch)
                    if to_annotate:
                        for annotate in to_annotate:
                            result["annotates_{}".format("to_annotate" if len(relation) == 1 else "to_ommit")].append(
                                annotate
                            )
                else:
                    if hasattr(field, "__call__") or "<property object" in str(field):
                        result["relations_unknown"].append(relation)
                        # raise Exception(field)
                    else:
                        result["other"]["b"].append((str(type(field)), relation))
                    pass
            elif key == "all":
                del relation[-1]
                for key2, value2 in glu.items():
                    get_1relation(model, key2, value2, relation, prefetch=prefetch)
            else:
                # ---
                result["other"]["c"].append((str(type(model)), relation))

        for lookup, lookups_2 in lookups_map.items():
            dump_to_json_file(lookups_2, get_file_name("lookups_2"))
            for key, value in lookups_2.items():
                get_1relation(model, key, value, [])
        dump_to_json_file(result, get_file_name("get_relations"))
        return result

    def selectprefetch_related(queryset, confirmed_relations, prefetch=False):
        for relation in confirmed_relations:
            relation_string = "__".join(relation)
            if prefetch:
                queryset = queryset.prefetch_related(relation_string)
                result_list = prefetch_related_list
            else:
                queryset = queryset.select_related(relation_string)
                result_list = select_related_list
            result_list.append("__".join(relation))
        queryset.optimized = True
        return queryset

    def annotates(queryset):
        for annotate in relations["annotates_to_annotate"]:
            if hasattr(model, annotate):
                queryset = getattr(model, annotate)(queryset)
        return queryset

    from django.db.models.query import QuerySet

    add_double_underscore_str = True  # we will add __str__ to end of every lookup to search for @optimize_related
    conditions = []
    fornode = look_for_fornode(nodelist=get_nodes_from_template_name(template_name))
    queryset = queryset
    if fornode:
        # so we have first for (for now)
        conditions = []
        node_types = []
        if len(fornode.loopvars) == 1:
            fornode_var = fornode.loopvars[0]
        else:
            raise Exception("Many loop vars, how??")
        lookups = []
        sequences = []
        show_me_item_with_dots = []
        select_related_list = []
        prefetch_related_list = []
        model = get_object_from_queryset(queryset)
        globals()["general_result"] = dict()

        second_step(fornode, level=0, conditions_for_level=[])
        # dump_to_json_file(globals()["general_result"], get_file_name("aaa"))

        lookups_raw = lookups
        # lookups = list(filter(lambda ls: ls[0] == fornode_var, lookups))
        lookups = merge_lookups_using_sequences(lookups)
        lookups_map = get_lookups_map(lookups)
        # TODO check check_propagation var
        relations = get_relations(lookups_map=lookups_map, model=model, variable=fornode_var)
        queryset = selectprefetch_related(queryset, confirmed_relations=relations["relations_to_select"])
        queryset = selectprefetch_related(
            queryset, confirmed_relations=relations["relations_to_prefetch"], prefetch=True
        )
        queryset = annotates(queryset)
        dump_to_json_file(
            dict(
                date=now().isoformat(),
                queryset=str(queryset),
                model=str(model),
                fornode_var=fornode_var,
                lookups_list=lookups_raw,
                sequences=sequences,
                lookups_map=lookups_map,
                relations=relations,
                select_related_list=select_related_list,
                prefetch_related_list=prefetch_related_list,
            ),
            get_file_name("dashboard")
        )
        # raise Exception(show_me_item_with_dots)
        # dump_to_json_file(show_me_item_with_dots, get_file_name("show_me_item_with_dots"))

        # raise Exception(globals()['general_result'])
        return queryset
    else:
        raise Exception("ForNode not found")
    return queryset
